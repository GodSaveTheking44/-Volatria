#include "orderbook.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace volatria {

OrderBook::OrderBook() = default;
OrderBook::~OrderBook() = default;

// --------------------------------------------------------------------------
// Public API
// --------------------------------------------------------------------------

uint64_t OrderBook::submit_order(Order order) {
    // Validate
    if (order.quantity == 0) {
        order.status = OrderStatus::REJECTED;
        return 0;
    }
    if (order.type == OrderType::LIMIT && order.price <= 0.0) {
        order.status = OrderStatus::REJECTED;
        return 0;
    }

    // Assign ID and timestamp
    order.id = next_order_id();
    order.timestamp = next_timestamp();
    order.filled_quantity = 0;
    order.status = OrderStatus::ACCEPTED;

    // FOK pre-check: verify full quantity is available before matching
    if (order.tif == TimeInForce::FOK) {
        if (!can_fill_fok(order)) {
            order.status = OrderStatus::REJECTED;
            return 0;
        }
    }

    // Attempt matching
    match_order(order);

    // Post-match handling
    if (order.remaining_quantity() == 0) {
        order.status = OrderStatus::FILLED;
    } else if (order.filled_quantity > 0) {
        order.status = OrderStatus::PARTIALLY_FILLED;
    }

    // Rest on book or cancel remainder based on order type and TIF
    if (order.remaining_quantity() > 0 && !order.is_terminal()) {
        if (order.type == OrderType::MARKET) {
            // Market orders don't rest
            order.status = OrderStatus::CANCELLED;
        } else if (order.tif == TimeInForce::IOC) {
            // IOC: cancel unfilled remainder
            order.status = OrderStatus::CANCELLED;
        } else if (order.tif == TimeInForce::GTC) {
            // GTC limit order: rest on book
            add_to_book(order);
        }
    }

    return order.id;
}

bool OrderBook::cancel_order(uint64_t order_id) {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) {
        return false;
    }

    it->second.it->status = OrderStatus::CANCELLED;
    remove_from_book(order_id);
    return true;
}

void OrderBook::set_fill_callback(FillCallback callback) {
    fill_callback_ = std::move(callback);
}

std::vector<Level> OrderBook::get_bids(int depth) const {
    std::vector<Level> result;
    int count = 0;
    for (const auto& [price, queue] : bids_) {
        if (count >= depth) break;
        Level level;
        level.price = price;
        level.total_quantity = 0;
        level.order_count = 0;
        for (const auto& order : queue) {
            level.total_quantity += order.remaining_quantity();
            level.order_count++;
        }
        result.push_back(level);
        count++;
    }
    return result;
}

std::vector<Level> OrderBook::get_asks(int depth) const {
    std::vector<Level> result;
    int count = 0;
    for (const auto& [price, queue] : asks_) {
        if (count >= depth) break;
        Level level;
        level.price = price;
        level.total_quantity = 0;
        level.order_count = 0;
        for (const auto& order : queue) {
            level.total_quantity += order.remaining_quantity();
            level.order_count++;
        }
        result.push_back(level);
        count++;
    }
    return result;
}

std::optional<double> OrderBook::best_bid() const {
    if (bids_.empty()) return std::nullopt;
    return bids_.begin()->first;
}

std::optional<double> OrderBook::best_ask() const {
    if (asks_.empty()) return std::nullopt;
    return asks_.begin()->first;
}

std::optional<double> OrderBook::mid_price() const {
    auto bb = best_bid();
    auto ba = best_ask();
    if (!bb || !ba) return std::nullopt;
    return (*bb + *ba) / 2.0;
}

std::optional<double> OrderBook::spread() const {
    auto bb = best_bid();
    auto ba = best_ask();
    if (!bb || !ba) return std::nullopt;
    return *ba - *bb;
}

size_t OrderBook::order_count() const {
    return order_index_.size();
}

std::optional<Order> OrderBook::get_order(uint64_t order_id) const {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) return std::nullopt;
    return *(it->second.it);
}

const std::vector<Fill>& OrderBook::get_fills() const {
    return fill_history_;
}

// --------------------------------------------------------------------------
// Matching Engine
// --------------------------------------------------------------------------

void OrderBook::match_order(Order& order) {
    if (order.side == Side::BUY) {
        match_against_asks(order);
    } else {
        match_against_bids(order);
    }
}

void OrderBook::match_against_asks(Order& order) {
    // Incoming buy matches against resting asks (lowest price first)
    while (order.remaining_quantity() > 0 && !asks_.empty()) {
        auto level_it = asks_.begin();
        double ask_price = level_it->first;

        // For limit orders, stop if the ask price exceeds our limit
        if (order.type == OrderType::LIMIT && ask_price > order.price) {
            break;
        }

        auto& queue = level_it->second;
        while (order.remaining_quantity() > 0 && !queue.empty()) {
            auto& maker = queue.front();

            // Self-trade prevention check
            if (check_stp(maker, order)) {
                // STP was triggered. The maker may have been removed.
                // If the taker was cancelled by STP, stop matching.
                if (order.status == OrderStatus::CANCELLED) {
                    return;
                }
                // If the maker was cancelled, it's been removed from the queue.
                // If the entire price level was erased, break inner loop to avoid dangling reference.
                if (asks_.find(ask_price) == asks_.end()) {
                    break;
                }
                // Continue to the next order in the queue.
                continue;
            }

            // Determine fill quantity
            uint64_t fill_qty = std::min(order.remaining_quantity(),
                                         maker.remaining_quantity());

            // Execute the fill
            execute_fill(maker, order, fill_qty);

            // Remove fully filled maker from book
            if (maker.remaining_quantity() == 0) {
                maker.status = OrderStatus::FILLED;
                uint64_t maker_id = maker.id;
                queue.pop_front();
                order_index_.erase(maker_id);
            } else {
                maker.status = OrderStatus::PARTIALLY_FILLED;
            }
        }

        // Remove empty price level
        if (asks_.find(ask_price) != asks_.end()) {
            if (queue.empty()) {
                asks_.erase(level_it);
            }
        }
    }
}

void OrderBook::match_against_bids(Order& order) {
    // Incoming sell matches against resting bids (highest price first)
    while (order.remaining_quantity() > 0 && !bids_.empty()) {
        auto level_it = bids_.begin();
        double bid_price = level_it->first;

        // For limit orders, stop if the bid price is below our limit
        if (order.type == OrderType::LIMIT && bid_price < order.price) {
            break;
        }

        auto& queue = level_it->second;
        while (order.remaining_quantity() > 0 && !queue.empty()) {
            auto& maker = queue.front();

            // Self-trade prevention check
            if (check_stp(maker, order)) {
                if (order.status == OrderStatus::CANCELLED) {
                    return;
                }
                if (bids_.find(bid_price) == bids_.end()) {
                    break;
                }
                continue;
            }

            uint64_t fill_qty = std::min(order.remaining_quantity(),
                                         maker.remaining_quantity());

            execute_fill(maker, order, fill_qty);

            if (maker.remaining_quantity() == 0) {
                maker.status = OrderStatus::FILLED;
                uint64_t maker_id = maker.id;
                queue.pop_front();
                order_index_.erase(maker_id);
            } else {
                maker.status = OrderStatus::PARTIALLY_FILLED;
            }
        }

        if (bids_.find(bid_price) != bids_.end()) {
            if (queue.empty()) {
                bids_.erase(level_it);
            }
        }
    }
}

bool OrderBook::can_fill_fok(const Order& order) const {
    uint64_t available = 0;
    uint64_t needed = order.quantity;

    if (order.side == Side::BUY) {
        for (const auto& [price, queue] : asks_) {
            if (order.type == OrderType::LIMIT && price > order.price) {
                break;
            }
            for (const auto& resting : queue) {
                // Skip self-trades for FOK availability check
                if (order.stp_mode != STPMode::NONE &&
                    order.participant_id == resting.participant_id) {
                    continue;
                }
                available += resting.remaining_quantity();
                if (available >= needed) return true;
            }
        }
    } else {
        for (const auto& [price, queue] : bids_) {
            if (order.type == OrderType::LIMIT && price < order.price) {
                break;
            }
            for (const auto& resting : queue) {
                if (order.stp_mode != STPMode::NONE &&
                    order.participant_id == resting.participant_id) {
                    continue;
                }
                available += resting.remaining_quantity();
                if (available >= needed) return true;
            }
        }
    }

    return available >= needed;
}

// --------------------------------------------------------------------------
// Self-Trade Prevention
// --------------------------------------------------------------------------

bool OrderBook::check_stp(Order& maker, Order& taker) {
    // No STP if modes are NONE or participants differ
    if (taker.stp_mode == STPMode::NONE) return false;
    if (maker.participant_id != taker.participant_id) return false;

    switch (taker.stp_mode) {
        case STPMode::CANCEL_NEWEST: {
            // Cancel the incoming (taker) order
            taker.status = OrderStatus::CANCELLED;
            return true;
        }
        case STPMode::CANCEL_OLDEST: {
            // Cancel the resting (maker) order
            maker.status = OrderStatus::CANCELLED;
            remove_from_book(maker.id);
            return true;
        }
        case STPMode::CANCEL_BOTH: {
            // Cancel both orders
            taker.status = OrderStatus::CANCELLED;
            maker.status = OrderStatus::CANCELLED;
            remove_from_book(maker.id);
            return true;
        }
        default:
            return false;
    }
}

// --------------------------------------------------------------------------
// Book Management
// --------------------------------------------------------------------------

void OrderBook::add_to_book(Order order) {
    uint64_t order_id = order.id;
    Side side = order.side;
    double price = order.price;

    if (side == Side::BUY) {
        auto& queue = bids_[price];
        queue.push_back(std::move(order));
        auto it = std::prev(queue.end());
        order_index_[order_id] = {side, price, it};
    } else {
        auto& queue = asks_[price];
        queue.push_back(std::move(order));
        auto it = std::prev(queue.end());
        order_index_[order_id] = {side, price, it};
    }
}

void OrderBook::remove_from_book(uint64_t order_id) {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) return;

    auto& loc = it->second;
    if (loc.side == Side::BUY) {
        auto level_it = bids_.find(loc.price);
        if (level_it != bids_.end()) {
            level_it->second.erase(loc.it);
            if (level_it->second.empty()) {
                bids_.erase(level_it);
            }
        }
    } else {
        auto level_it = asks_.find(loc.price);
        if (level_it != asks_.end()) {
            level_it->second.erase(loc.it);
            if (level_it->second.empty()) {
                asks_.erase(level_it);
            }
        }
    }

    order_index_.erase(it);
}

void OrderBook::execute_fill(Order& maker, Order& taker, uint64_t fill_qty) {
    maker.filled_quantity += fill_qty;
    taker.filled_quantity += fill_qty;

    Fill fill;
    fill.maker_order_id = maker.id;
    fill.taker_order_id = taker.id;
    fill.maker_participant_id = maker.participant_id;
    fill.taker_participant_id = taker.participant_id;
    fill.aggressor_side = taker.side;
    fill.price = maker.price;  // Fill at resting (maker) price
    fill.quantity = fill_qty;
    fill.timestamp = next_timestamp();

    emit_fill(fill);
}

void OrderBook::emit_fill(const Fill& fill) {
    fill_history_.push_back(fill);
    if (fill_callback_) {
        fill_callback_(fill);
    }
}

// --------------------------------------------------------------------------
// ID Generation
// --------------------------------------------------------------------------

uint64_t OrderBook::next_order_id() {
    return next_order_id_++;
}

uint64_t OrderBook::next_timestamp() {
    return next_timestamp_++;
}

} // namespace volatria
