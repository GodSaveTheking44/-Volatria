#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "order.h"
#include "orderbook.h"
#include "black_scholes.h"
#include "binomial_tree.h"
#include "lsm_monte_carlo.h"

#include <sstream>

namespace py = pybind11;
using namespace volatria;

// ──────────────────────────────────────────────────────────────────────
// Helper: human-readable enum name formatters
// ──────────────────────────────────────────────────────────────────────

static const char* side_name(Side s) {
    switch (s) {
        case Side::BUY:  return "BUY";
        case Side::SELL: return "SELL";
    }
    return "?";
}

static const char* order_type_name(OrderType t) {
    switch (t) {
        case OrderType::LIMIT:  return "LIMIT";
        case OrderType::MARKET: return "MARKET";
    }
    return "?";
}

static const char* tif_name(TimeInForce t) {
    switch (t) {
        case TimeInForce::GTC: return "GTC";
        case TimeInForce::IOC: return "IOC";
        case TimeInForce::FOK: return "FOK";
    }
    return "?";
}

static const char* status_name(OrderStatus s) {
    switch (s) {
        case OrderStatus::NEW:              return "NEW";
        case OrderStatus::ACCEPTED:         return "ACCEPTED";
        case OrderStatus::PARTIALLY_FILLED: return "PARTIALLY_FILLED";
        case OrderStatus::FILLED:           return "FILLED";
        case OrderStatus::CANCELLED:        return "CANCELLED";
        case OrderStatus::REJECTED:         return "REJECTED";
    }
    return "?";
}

// ──────────────────────────────────────────────────────────────────────
// Module definition
// ──────────────────────────────────────────────────────────────────────

PYBIND11_MODULE(volatria_core_py, m) {
    m.doc() = "Volatria C++ order book bindings";

    // ── Enums ────────────────────────────────────────────────────────

    py::enum_<Side>(m, "Side")
        .value("BUY",  Side::BUY)
        .value("SELL", Side::SELL)
        .export_values();

    py::enum_<OrderType>(m, "OrderType")
        .value("LIMIT",  OrderType::LIMIT)
        .value("MARKET", OrderType::MARKET)
        .export_values();

    py::enum_<TimeInForce>(m, "TimeInForce")
        .value("GTC", TimeInForce::GTC)
        .value("IOC", TimeInForce::IOC)
        .value("FOK", TimeInForce::FOK)
        .export_values();

    py::enum_<STPMode>(m, "STPMode")
        .value("NONE_",          STPMode::NONE)
        .value("CANCEL_NEWEST",  STPMode::CANCEL_NEWEST)
        .value("CANCEL_OLDEST",  STPMode::CANCEL_OLDEST)
        .value("CANCEL_BOTH",    STPMode::CANCEL_BOTH)
        .export_values();

    py::enum_<OrderStatus>(m, "OrderStatus")
        .value("NEW",              OrderStatus::NEW)
        .value("ACCEPTED",         OrderStatus::ACCEPTED)
        .value("PARTIALLY_FILLED", OrderStatus::PARTIALLY_FILLED)
        .value("FILLED",           OrderStatus::FILLED)
        .value("CANCELLED",        OrderStatus::CANCELLED)
        .value("REJECTED",         OrderStatus::REJECTED)
        .export_values();

    // ── Order struct ─────────────────────────────────────────────────

    py::class_<Order>(m, "Order")
        .def(py::init<>())
        .def_readwrite("id",              &Order::id)
        .def_readwrite("participant_id",  &Order::participant_id)
        .def_readwrite("side",            &Order::side)
        .def_readwrite("type",            &Order::type)
        .def_readwrite("tif",             &Order::tif)
        .def_readwrite("stp_mode",        &Order::stp_mode)
        .def_readwrite("status",          &Order::status)
        .def_readwrite("price",           &Order::price)
        .def_readwrite("quantity",        &Order::quantity)
        .def_readwrite("filled_quantity", &Order::filled_quantity)
        .def_readwrite("timestamp",       &Order::timestamp)
        .def("remaining_quantity",        &Order::remaining_quantity,
             "Returns quantity - filled_quantity")
        .def("__repr__", [](const Order& o) {
            std::ostringstream os;
            os << "Order(id=" << o.id
               << ", side=" << side_name(o.side)
               << ", type=" << order_type_name(o.type)
               << ", tif=" << tif_name(o.tif)
               << ", price=" << o.price
               << ", qty=" << o.quantity
               << ", filled=" << o.filled_quantity
               << ", status=" << status_name(o.status) << ")";
            return os.str();
        });

    // ── Fill struct ──────────────────────────────────────────────────

    py::class_<Fill>(m, "Fill")
        .def(py::init<>())
        .def_readonly("maker_order_id",       &Fill::maker_order_id)
        .def_readonly("taker_order_id",       &Fill::taker_order_id)
        .def_readonly("maker_participant_id", &Fill::maker_participant_id)
        .def_readonly("taker_participant_id", &Fill::taker_participant_id)
        .def_readonly("aggressor_side",       &Fill::aggressor_side)
        .def_readonly("price",                &Fill::price)
        .def_readonly("quantity",             &Fill::quantity)
        .def_readonly("timestamp",            &Fill::timestamp)
        .def("__repr__", [](const Fill& f) {
            std::ostringstream os;
            os << "Fill(maker=" << f.maker_order_id
               << ", taker=" << f.taker_order_id
               << ", price=" << f.price
               << ", qty=" << f.quantity
               << ", side=" << side_name(f.aggressor_side) << ")";
            return os.str();
        });

    // ── Level struct ─────────────────────────────────────────────────

    py::class_<Level>(m, "Level")
        .def(py::init<>())
        .def_readonly("price",         &Level::price)
        .def_readonly("total_quantity", &Level::total_quantity)
        .def_readonly("order_count",   &Level::order_count)
        .def("__repr__", [](const Level& l) {
            std::ostringstream os;
            os << "Level(price=" << l.price
               << ", qty=" << l.total_quantity
               << ", orders=" << l.order_count << ")";
            return os.str();
        });

    // ── OrderBook class ──────────────────────────────────────────────

    py::class_<OrderBook>(m, "OrderBook")
        .def(py::init<>())

        // Core operations
        .def("submit_order",  &OrderBook::submit_order, py::arg("order"),
             "Submit an order and return its assigned ID")
        .def("submit_order_vals", [](OrderBook& self, Side side, OrderType type, double price, uint64_t quantity, uint64_t participant_id, TimeInForce tif, STPMode stp_mode) {
            Order order;
            order.side = side;
            order.type = type;
            order.price = price;
            order.quantity = quantity;
            order.participant_id = participant_id;
            order.tif = tif;
            order.stp_mode = stp_mode;
            return self.submit_order(order);
        }, py::arg("side"), py::arg("type"), py::arg("price"), py::arg("quantity"), py::arg("participant_id") = 1, py::arg("tif") = TimeInForce::GTC, py::arg("stp_mode") = STPMode::NONE,
        "Submit an order by value fields directly to avoid pybind11 property overhead")
        .def("cancel_order",  &OrderBook::cancel_order, py::arg("order_id"),
             "Cancel an order by ID; returns True if cancelled")

        // Callback
        .def("set_fill_callback", &OrderBook::set_fill_callback,
             py::arg("callback"),
             "Register a Python callable invoked on each fill")

        // Book state queries
        .def("get_bids",   &OrderBook::get_bids,  py::arg("depth") = 10,
             "Top bid levels (descending by price)")
        .def("get_asks",   &OrderBook::get_asks,  py::arg("depth") = 10,
             "Top ask levels (ascending by price)")
        .def("best_bid",   &OrderBook::best_bid,
             "Best bid price, or None")
        .def("best_ask",   &OrderBook::best_ask,
             "Best ask price, or None")
        .def("mid_price",  &OrderBook::mid_price,
             "Mid price, or None if one side is empty")
        .def("spread",     &OrderBook::spread,
             "Spread, or None if one side is empty")
        .def("order_count", &OrderBook::order_count,
             "Number of resting orders")
        .def("get_order",  &OrderBook::get_order, py::arg("order_id"),
             "Retrieve a resting order by ID, or None")
        .def("get_fills",  &OrderBook::get_fills,
             py::return_value_policy::reference_internal,
             "All fill events that have occurred");

    // ── Module-level Option Pricing Functions ─────────────────────────
    m.def("black_scholes_price", &black_scholes_price, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("is_call"),
          "Calculate Black-Scholes analytical price for a European option");
    m.def("bs_delta", &bs_delta, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("is_call"),
          "Calculate Black-Scholes Delta");
    m.def("bs_gamma", &bs_gamma, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"),
          "Calculate Black-Scholes Gamma");
    m.def("bs_vega", &bs_vega, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"),
          "Calculate Black-Scholes Vega");
    m.def("bs_theta", &bs_theta, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("is_call"),
          "Calculate Black-Scholes Theta");
    m.def("bs_rho", &bs_rho, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("is_call"),
          "Calculate Black-Scholes Rho");
    m.def("bs_implied_volatility", &bs_implied_volatility, py::arg("market_price"), py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("is_call"), py::arg("tol") = 1e-6, py::arg("max_iter") = 100,
          "Calculate Black-Scholes Implied Volatility");
    m.def("binomial_tree_price", &binomial_tree_price, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("steps"), py::arg("is_call"), py::arg("is_american"),
          "Calculate CRR Binomial Tree option price");
    m.def("lsm_monte_carlo_price", &lsm_monte_carlo_price, py::arg("S"), py::arg("K"), py::arg("r"), py::arg("T"), py::arg("sigma"), py::arg("paths"), py::arg("steps"), py::arg("is_call"), py::arg("is_american"), py::arg("seed") = 42,
          "Calculate Longstaff-Schwartz Monte Carlo option price");
}
