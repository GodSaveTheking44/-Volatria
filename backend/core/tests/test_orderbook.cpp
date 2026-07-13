// ---------------------------------------------------------------------------
// Volatria OrderBook — Google Test Suite
// ---------------------------------------------------------------------------
// Covers: basic operations, matching engine, partial fills, cancellation,
//         self-trade prevention, time-in-force semantics, callbacks, and
//         input validation.
// ---------------------------------------------------------------------------

#include <gtest/gtest.h>
#include "orderbook.h"

#include <cstdint>
#include <optional>
#include <vector>

using namespace volatria;

// ===========================================================================
// Fixture
// ===========================================================================

class OrderBookTest : public ::testing::Test {
protected:
    OrderBook book;
    std::vector<Fill> fills;  // Collects callback fills

    void SetUp() override {
        book.set_fill_callback([this](const Fill& f) {
            fills.push_back(f);
        });
    }

    // ----- helpers ---------------------------------------------------------

    // Create a GTC limit order with sensible defaults.
    static Order make_limit(Side side, double price, uint64_t qty,
                            uint64_t participant_id = 1,
                            STPMode stp = STPMode::NONE,
                            TimeInForce tif = TimeInForce::GTC) {
        Order o;
        o.side            = side;
        o.type            = OrderType::LIMIT;
        o.tif             = tif;
        o.stp_mode        = stp;
        o.price           = price;
        o.quantity         = qty;
        o.participant_id  = participant_id;
        return o;
    }

    // Create a market order.
    static Order make_market(Side side, uint64_t qty,
                             uint64_t participant_id = 1,
                             STPMode stp = STPMode::NONE) {
        Order o;
        o.side            = side;
        o.type            = OrderType::MARKET;
        o.tif             = TimeInForce::GTC;   // TIF is moot for market
        o.stp_mode        = stp;
        o.price           = 0.0;
        o.quantity         = qty;
        o.participant_id  = participant_id;
        return o;
    }

    // Seed the book with a simple two-sided market:
    //   bid 99.0 x 10,  ask 101.0 x 10
    void seed_simple_market() {
        book.submit_order(make_limit(Side::BUY,  99.0, 10));
        book.submit_order(make_limit(Side::SELL, 101.0, 10));
    }
};

// ===========================================================================
// Basic Operations
// ===========================================================================

TEST_F(OrderBookTest, EmptyBookState) {
    // An untouched book must have no bids, no asks, and no best prices.
    EXPECT_TRUE(book.get_bids().empty());
    EXPECT_TRUE(book.get_asks().empty());
    EXPECT_EQ(book.best_bid(), std::nullopt);
    EXPECT_EQ(book.best_ask(), std::nullopt);
    EXPECT_EQ(book.mid_price(), std::nullopt);
    EXPECT_EQ(book.spread(), std::nullopt);
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_TRUE(book.get_fills().empty());
}

TEST_F(OrderBookTest, LimitBuyOrderRests) {
    // A limit buy below the best ask (or on an empty book) rests passively.
    uint64_t id = book.submit_order(make_limit(Side::BUY, 100.0, 5));
    EXPECT_NE(id, 0u);
    EXPECT_EQ(book.order_count(), 1u);

    auto bids = book.get_bids();
    ASSERT_EQ(bids.size(), 1u);
    EXPECT_DOUBLE_EQ(bids[0].price, 100.0);
    EXPECT_EQ(bids[0].total_quantity, 5u);
    EXPECT_EQ(bids[0].order_count, 1);
    EXPECT_TRUE(fills.empty());         // No match occurred
}

TEST_F(OrderBookTest, LimitSellOrderRests) {
    // A limit sell above the best bid (or on an empty book) rests passively.
    uint64_t id = book.submit_order(make_limit(Side::SELL, 100.0, 7));
    EXPECT_NE(id, 0u);
    EXPECT_EQ(book.order_count(), 1u);

    auto asks = book.get_asks();
    ASSERT_EQ(asks.size(), 1u);
    EXPECT_DOUBLE_EQ(asks[0].price, 100.0);
    EXPECT_EQ(asks[0].total_quantity, 7u);
    EXPECT_EQ(asks[0].order_count, 1);
    EXPECT_TRUE(fills.empty());
}

TEST_F(OrderBookTest, BestBidAskSpread) {
    seed_simple_market();               // bid 99 x 10, ask 101 x 10

    EXPECT_DOUBLE_EQ(book.best_bid().value(), 99.0);
    EXPECT_DOUBLE_EQ(book.best_ask().value(), 101.0);
    EXPECT_DOUBLE_EQ(book.spread().value(), 2.0);
    EXPECT_DOUBLE_EQ(book.mid_price().value(), 100.0);
    EXPECT_EQ(book.order_count(), 2u);
}

// ===========================================================================
// Matching
// ===========================================================================

TEST_F(OrderBookTest, LimitOrderCrossMatch) {
    // Resting ask at 101.  Incoming limit buy at 101 crosses — fill at maker
    // price (101).
    book.submit_order(make_limit(Side::SELL, 101.0, 10, /*pid=*/2));
    uint64_t buy_id = book.submit_order(make_limit(Side::BUY, 101.0, 10));

    ASSERT_EQ(fills.size(), 1u);
    EXPECT_DOUBLE_EQ(fills[0].price, 101.0);   // maker price
    EXPECT_EQ(fills[0].quantity, 10u);
    EXPECT_EQ(fills[0].taker_order_id, buy_id);
    EXPECT_EQ(fills[0].aggressor_side, Side::BUY);

    // Both sides should be empty after full fill.
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_TRUE(book.get_bids().empty());
    EXPECT_TRUE(book.get_asks().empty());
}

TEST_F(OrderBookTest, MarketOrderFillsAgainstBook) {
    // Build two ask levels: 100 x 5, 101 x 5.
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    book.submit_order(make_limit(Side::SELL, 101.0, 5, 3));

    // Market buy for 10 sweeps both levels.
    uint64_t buy_id = book.submit_order(make_market(Side::BUY, 10));
    EXPECT_NE(buy_id, 0u);

    ASSERT_EQ(fills.size(), 2u);
    // First fill at 100
    EXPECT_DOUBLE_EQ(fills[0].price, 100.0);
    EXPECT_EQ(fills[0].quantity, 5u);
    // Second fill at 101
    EXPECT_DOUBLE_EQ(fills[1].price, 101.0);
    EXPECT_EQ(fills[1].quantity, 5u);

    EXPECT_EQ(book.order_count(), 0u);  // Book is clean
}

TEST_F(OrderBookTest, MarketOrderPartialFillEmptyBook) {
    // Only 5 available on the ask side; market buy for 10 fills 5 and the
    // remaining 5 is cancelled (market orders don't rest).
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    uint64_t buy_id = book.submit_order(make_market(Side::BUY, 10));

    EXPECT_NE(buy_id, 0u);
    ASSERT_EQ(fills.size(), 1u);
    EXPECT_EQ(fills[0].quantity, 5u);

    // Market order should NOT rest on the book.
    EXPECT_EQ(book.order_count(), 0u);
}

TEST_F(OrderBookTest, PriceTimePriority) {
    // Two resting sells at the same price; the earlier one must fill first.
    uint64_t ask1 = book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    uint64_t ask2 = book.submit_order(make_limit(Side::SELL, 100.0, 5, 3));

    // Buy 5 — should match against ask1 (time priority).
    book.submit_order(make_limit(Side::BUY, 100.0, 5));

    ASSERT_EQ(fills.size(), 1u);
    EXPECT_EQ(fills[0].maker_order_id, ask1);
    EXPECT_EQ(fills[0].quantity, 5u);

    // ask2 should still be resting.
    auto remaining = book.get_order(ask2);
    ASSERT_TRUE(remaining.has_value());
    EXPECT_EQ(remaining->remaining_quantity(), 5u);
}

TEST_F(OrderBookTest, MultipleLevelSweep) {
    // Build 3 ask levels.
    book.submit_order(make_limit(Side::SELL, 100.0, 3, 2));
    book.submit_order(make_limit(Side::SELL, 101.0, 4, 3));
    book.submit_order(make_limit(Side::SELL, 102.0, 5, 4));

    // Aggressive buy sweeping through all three levels.
    book.submit_order(make_limit(Side::BUY, 102.0, 12));

    // 3 fills: 3@100 + 4@101 + 5@102 = 12
    ASSERT_EQ(fills.size(), 3u);
    EXPECT_DOUBLE_EQ(fills[0].price, 100.0);
    EXPECT_EQ(fills[0].quantity, 3u);
    EXPECT_DOUBLE_EQ(fills[1].price, 101.0);
    EXPECT_EQ(fills[1].quantity, 4u);
    EXPECT_DOUBLE_EQ(fills[2].price, 102.0);
    EXPECT_EQ(fills[2].quantity, 5u);

    EXPECT_EQ(book.order_count(), 0u);
}

// ===========================================================================
// Partial Fills
// ===========================================================================

TEST_F(OrderBookTest, PartialFillRestingOrder) {
    // Resting ask 100 x 10.  Incoming buy 100 x 15 fills 10, residual 5 rests.
    uint64_t ask_id = book.submit_order(make_limit(Side::SELL, 100.0, 10, 2));
    uint64_t buy_id = book.submit_order(make_limit(Side::BUY, 100.0, 15));

    ASSERT_EQ(fills.size(), 1u);
    EXPECT_EQ(fills[0].quantity, 10u);

    // The residual 5 should be resting on the bid side.
    auto bid = book.get_order(buy_id);
    ASSERT_TRUE(bid.has_value());
    EXPECT_EQ(bid->remaining_quantity(), 5u);
    EXPECT_EQ(bid->filled_quantity, 10u);
    EXPECT_EQ(bid->status, OrderStatus::PARTIALLY_FILLED);

    // The ask side should be empty.
    EXPECT_TRUE(book.get_asks().empty());
}

TEST_F(OrderBookTest, CancelAfterPartialFill) {
    // Resting ask 100 x 5.  Incoming buy 100 x 10 fills 5, residual 5 rests.
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    uint64_t buy_id = book.submit_order(make_limit(Side::BUY, 100.0, 10));

    // Now cancel the partially-filled resting buy.
    EXPECT_TRUE(book.cancel_order(buy_id));

    // The order should no longer be on the book.
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_FALSE(book.get_order(buy_id).has_value());

    // But the fill that already happened must be preserved.
    ASSERT_EQ(book.get_fills().size(), 1u);
    EXPECT_EQ(book.get_fills()[0].quantity, 5u);
}

// ===========================================================================
// Cancel
// ===========================================================================

TEST_F(OrderBookTest, CancelOrder) {
    uint64_t id = book.submit_order(make_limit(Side::BUY, 99.0, 10));
    EXPECT_EQ(book.order_count(), 1u);

    EXPECT_TRUE(book.cancel_order(id));
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_FALSE(book.get_order(id).has_value());
    EXPECT_TRUE(book.get_bids().empty());
}

TEST_F(OrderBookTest, CancelNonexistentOrder) {
    EXPECT_FALSE(book.cancel_order(9999));
}

// ===========================================================================
// Self-Trade Prevention
// ===========================================================================

TEST_F(OrderBookTest, STPCancelNewest) {
    // Same participant (pid=1). Resting sell, incoming buy with CANCEL_NEWEST.
    book.submit_order(make_limit(Side::SELL, 100.0, 10, /*pid=*/1));
    uint64_t buy_id = book.submit_order(
        make_limit(Side::BUY, 100.0, 10, /*pid=*/1, STPMode::CANCEL_NEWEST));

    // Taker (incoming buy) should be cancelled — no fill.
    EXPECT_TRUE(fills.empty());
    // The resting sell should still be on the book.
    EXPECT_EQ(book.order_count(), 1u);
    EXPECT_FALSE(book.get_asks().empty());
}

TEST_F(OrderBookTest, STPCancelOldest) {
    // Same participant. Resting sell, incoming buy with CANCEL_OLDEST.
    uint64_t ask_id = book.submit_order(
        make_limit(Side::SELL, 100.0, 10, /*pid=*/1));
    uint64_t buy_id = book.submit_order(
        make_limit(Side::BUY, 100.0, 10, /*pid=*/1, STPMode::CANCEL_OLDEST));

    // Maker (resting sell) should be cancelled, taker rests if no further
    // contra.  Since no other asks remain, the buy rests.
    EXPECT_TRUE(fills.empty());
    EXPECT_FALSE(book.get_order(ask_id).has_value());   // maker gone

    // The buy should now be resting on the bid side.
    auto bids = book.get_bids();
    ASSERT_EQ(bids.size(), 1u);
    EXPECT_DOUBLE_EQ(bids[0].price, 100.0);
    EXPECT_EQ(bids[0].total_quantity, 10u);
}

TEST_F(OrderBookTest, STPCancelBoth) {
    // Same participant. CANCEL_BOTH removes both orders.
    book.submit_order(make_limit(Side::SELL, 100.0, 10, /*pid=*/1));
    book.submit_order(
        make_limit(Side::BUY, 100.0, 10, /*pid=*/1, STPMode::CANCEL_BOTH));

    EXPECT_TRUE(fills.empty());
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_TRUE(book.get_bids().empty());
    EXPECT_TRUE(book.get_asks().empty());
}

TEST_F(OrderBookTest, STPDifferentParticipants) {
    // Different participants — STP should NOT fire; normal fill occurs.
    book.submit_order(
        make_limit(Side::SELL, 100.0, 10, /*pid=*/1));
    book.submit_order(
        make_limit(Side::BUY, 100.0, 10, /*pid=*/2, STPMode::CANCEL_NEWEST));

    ASSERT_EQ(fills.size(), 1u);
    EXPECT_DOUBLE_EQ(fills[0].price, 100.0);
    EXPECT_EQ(fills[0].quantity, 10u);
    EXPECT_EQ(book.order_count(), 0u);
}

// ===========================================================================
// Time-in-Force
// ===========================================================================

TEST_F(OrderBookTest, IOCPartialFill) {
    // Resting ask 100 x 5.  IOC buy 100 x 10 fills 5, remainder cancelled.
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    uint64_t buy_id = book.submit_order(
        make_limit(Side::BUY, 100.0, 10, 1, STPMode::NONE, TimeInForce::IOC));

    ASSERT_EQ(fills.size(), 1u);
    EXPECT_EQ(fills[0].quantity, 5u);

    // The IOC remainder must NOT rest on the book.
    EXPECT_EQ(book.order_count(), 0u);
    EXPECT_FALSE(book.get_order(buy_id).has_value());
}

TEST_F(OrderBookTest, FOKRejectInsufficient) {
    // Only 5 available; FOK buy for 10 must be fully rejected (return 0).
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    uint64_t buy_id = book.submit_order(
        make_limit(Side::BUY, 100.0, 10, 1, STPMode::NONE, TimeInForce::FOK));

    EXPECT_EQ(buy_id, 0u);             // Rejected
    EXPECT_TRUE(fills.empty());        // No fills
    // The resting ask should be untouched.
    auto asks = book.get_asks();
    ASSERT_EQ(asks.size(), 1u);
    EXPECT_EQ(asks[0].total_quantity, 5u);
}

TEST_F(OrderBookTest, FOKFillSufficient) {
    // Enough liquidity: FOK succeeds and fills entirely.
    book.submit_order(make_limit(Side::SELL, 100.0, 10, 2));
    uint64_t buy_id = book.submit_order(
        make_limit(Side::BUY, 100.0, 10, 1, STPMode::NONE, TimeInForce::FOK));

    EXPECT_NE(buy_id, 0u);
    ASSERT_EQ(fills.size(), 1u);
    EXPECT_EQ(fills[0].quantity, 10u);
    EXPECT_EQ(book.order_count(), 0u);
}

// ===========================================================================
// Callbacks & Fill History
// ===========================================================================

TEST_F(OrderBookTest, FillCallbackFired) {
    // Verify the callback receives correct price, qty, and order IDs.
    uint64_t ask_id = book.submit_order(make_limit(Side::SELL, 50.0, 3, 2));
    uint64_t buy_id = book.submit_order(make_limit(Side::BUY, 50.0, 3));

    ASSERT_EQ(fills.size(), 1u);
    const Fill& f = fills[0];
    EXPECT_EQ(f.maker_order_id, ask_id);
    EXPECT_EQ(f.taker_order_id, buy_id);
    EXPECT_EQ(f.maker_participant_id, 2u);
    EXPECT_EQ(f.taker_participant_id, 1u);
    EXPECT_EQ(f.aggressor_side, Side::BUY);
    EXPECT_DOUBLE_EQ(f.price, 50.0);
    EXPECT_EQ(f.quantity, 3u);
    EXPECT_GT(f.timestamp, 0u);
}

TEST_F(OrderBookTest, FillHistoryTracked) {
    // Multiple fills should all appear in get_fills().
    book.submit_order(make_limit(Side::SELL, 100.0, 5, 2));
    book.submit_order(make_limit(Side::SELL, 101.0, 5, 3));
    book.submit_order(make_limit(Side::BUY, 101.0, 10));

    const auto& history = book.get_fills();
    ASSERT_EQ(history.size(), 2u);
    EXPECT_DOUBLE_EQ(history[0].price, 100.0);
    EXPECT_EQ(history[0].quantity, 5u);
    EXPECT_DOUBLE_EQ(history[1].price, 101.0);
    EXPECT_EQ(history[1].quantity, 5u);
}

// ===========================================================================
// Validation / Rejection
// ===========================================================================

TEST_F(OrderBookTest, RejectZeroQuantity) {
    uint64_t id = book.submit_order(make_limit(Side::BUY, 100.0, 0));
    EXPECT_EQ(id, 0u);
    EXPECT_EQ(book.order_count(), 0u);
}

TEST_F(OrderBookTest, RejectNegativePrice) {
    // Negative price
    uint64_t id1 = book.submit_order(make_limit(Side::BUY, -1.0, 10));
    EXPECT_EQ(id1, 0u);

    // Zero price (limit orders)
    uint64_t id2 = book.submit_order(make_limit(Side::SELL, 0.0, 10));
    EXPECT_EQ(id2, 0u);

    EXPECT_EQ(book.order_count(), 0u);
}
