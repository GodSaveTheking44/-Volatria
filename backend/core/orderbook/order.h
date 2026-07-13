#pragma once

#include <cstdint>
#include <string>

namespace volatria {

enum class Side : uint8_t {
    BUY,
    SELL
};

enum class OrderType : uint8_t {
    LIMIT,
    MARKET
};

enum class TimeInForce : uint8_t {
    GTC,  // Good-til-cancelled (rests on book)
    IOC,  // Immediate-or-cancel (fill what you can, cancel rest)
    FOK   // Fill-or-kill (all or nothing)
};

enum class STPMode : uint8_t {
    NONE,            // No self-trade prevention
    CANCEL_NEWEST,   // Cancel the incoming (taker) order
    CANCEL_OLDEST,   // Cancel the resting (maker) order
    CANCEL_BOTH      // Cancel both orders
};

enum class OrderStatus : uint8_t {
    NEW,
    ACCEPTED,
    PARTIALLY_FILLED,
    FILLED,
    CANCELLED,
    REJECTED
};

struct Order {
    uint64_t id = 0;
    uint64_t participant_id = 0;   // For self-trade prevention
    Side side = Side::BUY;
    OrderType type = OrderType::LIMIT;
    TimeInForce tif = TimeInForce::GTC;
    STPMode stp_mode = STPMode::NONE;
    OrderStatus status = OrderStatus::NEW;
    double price = 0.0;            // Ignored for market orders
    uint64_t quantity = 0;         // Original quantity
    uint64_t filled_quantity = 0;  // Cumulative filled quantity
    uint64_t timestamp = 0;       // Set by the book on submission

    uint64_t remaining_quantity() const {
        return quantity - filled_quantity;
    }

    bool is_terminal() const {
        return status == OrderStatus::FILLED ||
               status == OrderStatus::CANCELLED ||
               status == OrderStatus::REJECTED;
    }
};

struct Fill {
    uint64_t maker_order_id = 0;
    uint64_t taker_order_id = 0;
    uint64_t maker_participant_id = 0;
    uint64_t taker_participant_id = 0;
    Side aggressor_side = Side::BUY;
    double price = 0.0;
    uint64_t quantity = 0;
    uint64_t timestamp = 0;
};

struct Level {
    double price = 0.0;
    uint64_t total_quantity = 0;
    int order_count = 0;
};

} // namespace volatria
