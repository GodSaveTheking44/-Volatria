#pragma once

#include "order.h"

#include <cstdint>
#include <functional>
#include <list>
#include <map>
#include <optional>
#include <unordered_map>
#include <vector>

namespace volatria {

class OrderBook {
public:
    using FillCallback = std::function<void(const Fill&)>;

    OrderBook();
    ~OrderBook();

    // --- Core operations ---

    // Submit an order. Returns the assigned order ID.
    // The order's id and timestamp fields are set by the book.
    uint64_t submit_order(Order order);

    // Cancel an order by ID. Returns true if the order was found and cancelled.
    bool cancel_order(uint64_t order_id);

    // --- Callbacks ---

    // Register a callback invoked synchronously on each fill during matching.
    void set_fill_callback(FillCallback callback);

    // --- Book state queries ---

    // Returns top-of-book bid levels, sorted descending by price.
    std::vector<Level> get_bids(int depth = 10) const;

    // Returns top-of-book ask levels, sorted ascending by price.
    std::vector<Level> get_asks(int depth = 10) const;

    // Best bid price, or std::nullopt if no bids.
    std::optional<double> best_bid() const;

    // Best ask price, or std::nullopt if no asks.
    std::optional<double> best_ask() const;

    // Mid price = (best_bid + best_ask) / 2, or std::nullopt if either side is empty.
    std::optional<double> mid_price() const;

    // Spread = best_ask - best_bid, or std::nullopt if either side is empty.
    std::optional<double> spread() const;

    // Total number of resting orders on the book.
    size_t order_count() const;

    // Retrieve a resting order by ID, or std::nullopt if not found.
    std::optional<Order> get_order(uint64_t order_id) const;

    // Get all fill events that have occurred.
    const std::vector<Fill>& get_fills() const;

private:
    // --- Internal types ---

    // An entry in the order queue at a given price level.
    // We store orders in a std::list for stable iterators and O(1) removal.
    using OrderQueue = std::list<Order>;

    // Bid side: descending price order (highest price first).
    using BidMap = std::map<double, OrderQueue, std::greater<double>>;

    // Ask side: ascending price order (lowest price first).
    using AskMap = std::map<double, OrderQueue>;

    // For O(1) cancel: maps order_id -> (side, price, iterator into the list).
    struct OrderLocation {
        Side side;
        double price;
        OrderQueue::iterator it;
    };
    using OrderIndex = std::unordered_map<uint64_t, OrderLocation>;

    // --- Internal methods ---

    uint64_t next_order_id();
    uint64_t next_timestamp();

    // Attempt to match an incoming order against the opposite side.
    // Modifies the order in-place (updating filled_quantity).
    void match_order(Order& order);

    // Try to match against bid side (incoming is a sell).
    void match_against_bids(Order& order);

    // Try to match against ask side (incoming is a buy).
    void match_against_asks(Order& order);

    // Check if a FOK order can be fully filled.
    bool can_fill_fok(const Order& order) const;

    // Add an order to the resting book.
    void add_to_book(Order order);

    // Remove an order from the book by its location.
    void remove_from_book(uint64_t order_id);

    // Execute a fill between maker and taker.
    void execute_fill(Order& maker, Order& taker, uint64_t fill_qty);

    // Self-trade prevention check. Returns true if the match should be blocked.
    // May modify/remove orders depending on the STP mode.
    bool check_stp(Order& maker, Order& taker);

    // Emit a fill event.
    void emit_fill(const Fill& fill);

    // --- Data ---

    BidMap bids_;
    AskMap asks_;
    OrderIndex order_index_;
    FillCallback fill_callback_;
    std::vector<Fill> fill_history_;

    uint64_t next_order_id_ = 1;
    uint64_t next_timestamp_ = 1;
};

} // namespace volatria
