import sqlite3
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "votes.db"):
        self.db_path = db_path

    def init_db(self):
        """Initialize the database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create votes table
                cursor.execute("""
                               CREATE TABLE IF NOT EXISTS votes
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   model_name
                                   TEXT
                                   NOT
                                   NULL,
                                   session_id
                                   TEXT
                                   NOT
                                   NULL,
                                   timestamp
                                   DATETIME
                                   NOT
                                   NULL,
                                   UNIQUE
                               (
                                   session_id
                               )
                                   )
                               """)

                conn.commit()
                logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def has_voted(self, session_id: str) -> bool:
        """Check if a session has already voted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM votes WHERE session_id = ?",
                    (session_id,)
                )
                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            logger.error(f"Error checking vote status: {e}")
            return False

    def record_vote(self, model_name: str, session_id: str):
        """Record a vote for a model"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO votes (model_name, session_id, timestamp)
                    VALUES (?, ?, ?)
                    """,
                    (model_name, session_id, datetime.now())
                )
                conn.commit()
                logger.info(f"Vote recorded: {model_name} for session {session_id}")

        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate vote attempt for session {session_id}")
            raise ValueError("Session has already voted")
        except Exception as e:
            logger.error(f"Error recording vote: {e}")
            raise

    def get_scores(self) -> Dict[str, int]:
        """Get vote counts for all models"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT model_name, COUNT(*) as vote_count
                    FROM votes
                    GROUP BY model_name
                    ORDER BY vote_count DESC
                    """
                )

                results = cursor.fetchall()

                # Initialize all models with 0 votes
                scores = {
                    'OpenAI': 0,
                    'Anthropic': 0,
                    'Gemini': 0,
                    'Llama': 0
                }

                # Update with actual vote counts
                for model_name, vote_count in results:
                    if model_name in scores:
                        scores[model_name] = vote_count

                return scores

        except Exception as e:
            logger.error(f"Error getting scores: {e}")
            return {'OpenAI': 0, 'Anthropic': 0, 'Gemini': 0, 'Llama': 0}

    def get_total_votes(self) -> int:
        """Get total number of votes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM votes")
                return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"Error getting total votes: {e}")
            return 0