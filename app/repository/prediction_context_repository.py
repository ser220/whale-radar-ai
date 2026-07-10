import json
import sqlite3
from typing import List, Optional

from app.config import DB_PATH
from app.domain.prediction_context import PredictionContext


class PredictionContextRepository:

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self):

        with self._connect() as conn:

            conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_context(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                prediction_id INTEGER UNIQUE,

                asset TEXT,

                market_regime TEXT,
                market_heat REAL,
                wallet_behaviour TEXT,

                asset_trend TEXT,
                btc_trend TEXT,
                eth_trend TEXT,

                volatility_regime TEXT,
                atr_percent REAL,

                funding_rate REAL,
                open_interest_change REAL,

                session TEXT,
                weekday TEXT,
                hour_utc INTEGER,

                captured_at TEXT,
                source TEXT,

                metadata TEXT
            )
            """)

            conn.commit()

    def save(
        self,
        context: PredictionContext,
    ) -> PredictionContext:

        with self._connect() as conn:

            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO prediction_context(

                    prediction_id,
                    asset,

                    market_regime,
                    market_heat,
                    wallet_behaviour,

                    asset_trend,
                    btc_trend,
                    eth_trend,

                    volatility_regime,
                    atr_percent,

                    funding_rate,
                    open_interest_change,

                    session,
                    weekday,
                    hour_utc,

                    captured_at,
                    source,

                    metadata

                )
                VALUES(
                    ?,?,?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?
                )
                """,
                (
                    context.prediction_id,
                    context.asset,

                    context.market_regime,
                    context.market_heat,
                    context.wallet_behaviour,

                    context.asset_trend,
                    context.btc_trend,
                    context.eth_trend,

                    context.volatility_regime,
                    context.atr_percent,

                    context.funding_rate,
                    context.open_interest_change,

                    context.session,
                    context.weekday,
                    context.hour_utc,

                    context.captured_at,
                    context.source,

                    json.dumps(context.metadata),
                ),
            )

            conn.commit()

            context.context_id = cursor.lastrowid

        return context

    def get(
        self,
        prediction_id: int,
    ) -> Optional[PredictionContext]:

        with self._connect() as conn:

            row = conn.execute(
                """
                SELECT *
                FROM prediction_context
                WHERE prediction_id=?
                """,
                (prediction_id,),
            ).fetchone()

        if row is None:
            return None

        return PredictionContext(

            context_id=row["id"],

            prediction_id=row["prediction_id"],
            asset=row["asset"],

            market_regime=row["market_regime"],
            market_heat=row["market_heat"],
            wallet_behaviour=row["wallet_behaviour"],

            asset_trend=row["asset_trend"],
            btc_trend=row["btc_trend"],
            eth_trend=row["eth_trend"],

            volatility_regime=row["volatility_regime"],
            atr_percent=row["atr_percent"],

            funding_rate=row["funding_rate"],
            open_interest_change=row["open_interest_change"],

            session=row["session"],
            weekday=row["weekday"],
            hour_utc=row["hour_utc"],

            captured_at=row["captured_at"],
            source=row["source"],

            metadata=json.loads(
                row["metadata"] or "{}"
            ),
        )

    def list(
        self,
        limit: int = 100,
    ) -> List[PredictionContext]:

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT *
                FROM prediction_context
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            self.get(
                row["prediction_id"]
            )
            for row in rows
        ]
