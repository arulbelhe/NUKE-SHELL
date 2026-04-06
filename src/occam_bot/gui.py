from __future__ import annotations

import random
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .engine import DecisionEngine, RiskConfig
from .models import MarketSignal


class OccamBotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Occam Logistics Bot (Windows 10)")
        self.geometry("980x620")

        self.running = False
        self.config_state = RiskConfig()
        self.engine = DecisionEngine(self.config_state)

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(root)
        controls.pack(fill=tk.X, pady=(0, 8))

        self.btn_start = ttk.Button(controls, text="Start Paper Bot", command=self.start)
        self.btn_stop = ttk.Button(controls, text="Stop", command=self.stop, state=tk.DISABLED)
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop.pack(side=tk.LEFT, padx=8)

        ttk.Label(
            controls,
            text="Safety: starts in PAPER mode only. Connect live execution after wallet/API review.",
        ).pack(side=tk.LEFT, padx=12)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab_signals = ttk.Frame(notebook)
        tab_trades = ttk.Frame(notebook)
        tab_config = ttk.Frame(notebook)

        notebook.add(tab_signals, text="Signals")
        notebook.add(tab_trades, text="Decisions")
        notebook.add(tab_config, text="Risk Config")

        self.signal_box = tk.Text(tab_signals, wrap=tk.WORD, height=20)
        self.trade_box = tk.Text(tab_trades, wrap=tk.WORD, height=20)
        self.signal_box.pack(fill=tk.BOTH, expand=True)
        self.trade_box.pack(fill=tk.BOTH, expand=True)

        self.vars = {
            "bankroll_usd": tk.StringVar(value=str(self.config_state.bankroll_usd)),
            "max_position_pct": tk.StringVar(value=str(self.config_state.max_position_pct)),
            "min_ev": tk.StringVar(value=str(self.config_state.min_ev)),
            "min_liquidity": tk.StringVar(value=str(self.config_state.min_liquidity)),
            "kelly_scale": tk.StringVar(value=str(self.config_state.kelly_scale)),
        }

        for idx, (key, var) in enumerate(self.vars.items()):
            ttk.Label(tab_config, text=key).grid(row=idx, column=0, sticky="w", padx=4, pady=4)
            ttk.Entry(tab_config, textvariable=var, width=20).grid(row=idx, column=1, sticky="w", padx=4, pady=4)

        ttk.Button(tab_config, text="Apply Risk Settings", command=self.apply_config).grid(
            row=len(self.vars), column=0, columnspan=2, sticky="w", padx=4, pady=10
        )

    def apply_config(self) -> None:
        try:
            self.config_state = RiskConfig(
                bankroll_usd=float(self.vars["bankroll_usd"].get()),
                max_position_pct=float(self.vars["max_position_pct"].get()),
                min_ev=float(self.vars["min_ev"].get()),
                min_liquidity=float(self.vars["min_liquidity"].get()),
                kelly_scale=float(self.vars["kelly_scale"].get()),
            )
            self.engine = DecisionEngine(self.config_state)
            self._log(self.trade_box, "Updated risk config.\n")
        except ValueError:
            self._log(self.trade_box, "Invalid config value(s).\n")

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        threading.Thread(target=self._run_paper_loop, daemon=True).start()

    def stop(self) -> None:
        self.running = False
        self.btn_start.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)

    def _run_paper_loop(self) -> None:
        while self.running:
            signal = self._mock_signal()
            self._log(
                self.signal_box,
                f"[{signal.detected_at:%H:%M:%S}] {signal.question} | mkt={signal.market_price:.2f} model={signal.model_probability:.2f} liq=${signal.liquidity:,.0f}\n",
            )

            decision = self.engine.evaluate(signal)
            if decision:
                self._log(
                    self.trade_box,
                    f"{decision.side} {decision.market_id} ${decision.size_usd:.2f} | {decision.rationale}\n",
                )
            time.sleep(2)

    @staticmethod
    def _mock_signal() -> MarketSignal:
        market_price = random.uniform(0.2, 0.8)
        model_probability = min(max(market_price + random.uniform(-0.2, 0.2), 0.01), 0.99)
        return MarketSignal(
            market_id=f"MKT-{random.randint(1000, 9999)}",
            question=random.choice(
                [
                    "Will Fed cut rates by June 2026?",
                    "Will CPI YoY print below 2.5% next release?",
                    "Will ceasefire hold for 30 days?",
                ]
            ),
            market_price=market_price,
            model_probability=model_probability,
            liquidity=random.uniform(200, 12000),
            category=random.choice(["macro", "geopolitics", "crypto"]),
            detected_at=datetime.utcnow(),
        )

    @staticmethod
    def _log(widget: tk.Text, line: str) -> None:
        widget.insert(tk.END, line)
        widget.see(tk.END)


if __name__ == "__main__":
    app = OccamBotApp()
    app.mainloop()
