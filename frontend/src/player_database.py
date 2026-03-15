import os

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create the SQLAlchemy engine
DATABASE_URL = f"sqlite:///{os.path.join(os.getenv('DATA_DIR', '.'), 'player_database.db')}"
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Define Player model
class PlayerORM(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    distribution_score = Column(Float)
    offense_score = Column(Float)
    defense_score = Column(Float)
    modifier = Column(Float, default=0.0)
    notes = Column(String(500), default="")

# Create tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def add_player(name: str, distribution: float, offense: float, defense: float, modifier: float = 0.0, notes: str = ""):
    """Add a new player to the database."""
    session = Session()
    try:
        existing = session.query(PlayerORM).filter(PlayerORM.name.ilike(name)).first()
        if existing:
            st.error(f"A player named '{existing.name}' already exists. Please use a different name.")
            return
        new_player = PlayerORM(
            name=name,
            distribution_score=distribution,
            offense_score=offense,
            defense_score=defense,
            modifier=modifier,
            notes=notes
        )
        session.add(new_player)
        session.commit()
        st.success(f"Successfully added player: {name}")
    except Exception as e:
        st.error(f"Error adding player: {str(e)}")
    finally:
        session.close()

def delete_player(player_name: str):
    """Delete a player from the database."""
    session = Session()
    try:
        player = session.query(PlayerORM).filter_by(name=player_name).first()
        if player:
            session.delete(player)
            session.commit()
            st.success(f"Successfully deleted player: {player_name}")
        else:
            st.error(f"Player {player_name} not found.")
    except Exception as e:
        st.error(f"Error deleting player: {str(e)}")
    finally:
        session.close()

def update_player(name: str, distribution: float, offense: float, defense: float, modifier: float, notes: str):
    """Update an existing player's scores in the database."""
    session = Session()
    try:
        player = session.query(PlayerORM).filter_by(name=name).first()
        if player:
            player.distribution_score = distribution
            player.offense_score = offense
            player.defense_score = defense
            player.modifier = modifier
            player.notes = notes
            session.commit()
            st.success(f"Successfully updated player: {name}")
        else:
            st.error(f"Player {name} not found.")
    except Exception as e:
        st.error(f"Error updating player: {str(e)}")
    finally:
        session.close()

def get_player(name: str) -> dict:
    """Get a single player's data by name."""
    session = Session()
    try:
        player = session.query(PlayerORM).filter_by(name=name).first()
        if player:
            return {
                "name": player.name,
                "distribution": player.distribution_score,
                "offense": player.offense_score,
                "defense": player.defense_score,
                "modifier": player.modifier,
                "notes": player.notes
            }
        else:
            st.error(f"Player {name} not found.")
            return None
    except Exception as e:
        st.error(f"Error retrieving player: {str(e)}")
        return None
    finally:
        session.close()

def list_players() -> list[dict]:
    """List all players in the database."""
    session = Session()
    try:
        players = session.query(PlayerORM).all()
        if players:
            player_data = []
            for player in players:
                player_data.append({
                    "name": player.name,
                    "distribution": player.distribution_score,
                    "offense": player.offense_score,
                    "defense": player.defense_score,
                    "modifier": player.modifier,
                    "notes": player.notes
                })
            return player_data
        else:
            st.info("No players found in the database.")
            return []
    except Exception as e:
        st.error(f"Error retrieving players: {str(e)}")
        return []
    finally:
        session.close()