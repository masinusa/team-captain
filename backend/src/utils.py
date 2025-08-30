from typing import Literal, List, Dict, Any
import random
import os
import inspect

from pydantic import validate_call

from data_models import Player


def this_file_dir():
    """

    Note:
    - Does not have trailing slash"""
    frame = inspect.stack()[1]
    caller_file = frame.filename
    return os.path.dirname(os.path.abspath(caller_file))


def pop_player_with_attribute(
    players: list[Player],
    min_or_max: Literal["min", "max"],
    attribute: Literal["offense", "defense", "offense_defense_ratio", "distribution"],
) -> Player:
    """return and remove the player with the highest/lowest specified attribute"""
    if min_or_max == "min":
        func = min
    elif min_or_max == "max":
        func = max
    else:
        raise ValueError(f"Unsupported min_or_max value: {min_or_max}")

    player = func(players, key=lambda player: getattr(player, attribute))
    index = players.index(player)
    return players.pop(index)


def coin_flip(prob: float = 0.25):
    """Simulates a {prob} probability of a true or false return"""
    return random.random() < prob


@validate_call
def swap_items(lst: List, index1: int, index2: int):
    """
    Swaps two items in a list at the specified indices.

    Args:
        lst (list): The list to modify
        index1 (int): Index of the first item to swap
        index2 (int): Index of the second item to swap

    Returns:
        list: The modified list with items swapped

    Raises:
        IndexError: If either index is out of range
        TypeError: If lst is not a list
    """

    # Check if indices are within bounds
    if not (0 <= index1 < len(lst)) or not (0 <= index2 < len(lst)):
        raise IndexError(f"Index {index1}, {index2} out of range for list of length {len(lst)}")

    # Swap the items
    lst[index1], lst[index2] = lst[index2], lst[index1]

    return lst


@validate_call
def swap_items_copy(lst, index1, index2):
    """
    Creates a new list with two items swapped at the specified indices.

    Args:
        lst (list): The original list (unchanged)
        index1 (int): Index of the first item to swap
        index2 (int): Index of the second item to swap

    Returns:
        list: A new list with items swapped

    Raises:
        IndexError: If either index is out of range
        TypeError: If lst is not a list
    """
    # Check if indices are within bounds
    if not (0 <= index1 < len(lst)) or not (0 <= index2 < len(lst)):
        raise IndexError("Index out of range")

    # Create a copy and swap
    new_lst = lst.copy()
    new_lst[index1], new_lst[index2] = new_lst[index2], new_lst[index1]

    return new_lst


@validate_call
def swap_dict_keys(d: Dict, key1: Any, key2: Any):
    """
    Swaps two keys in a dictionary along with their values.

    Args:
        d (dict): The dictionary to modify
        key1: The first key to swap
        key2: The second key to swap

    Returns:
        dict: The modified dictionary with keys swapped

    Raises:
        KeyError: If either key is not found in the dictionary
        TypeError: If d is not a dictionary
    """
    # Input validation
    if not isinstance(d, dict):
        raise TypeError("First argument must be a dictionary")

    # Check if both keys exist
    if key1 not in d:
        raise KeyError(f"Key '{key1}' not found in dictionary")
    if key2 not in d:
        raise KeyError(f"Key '{key2}' not found in dictionary")

    # Store the values
    value1 = d[key1]
    value2 = d[key2]

    # Remove the old keys
    del d[key1]
    del d[key2]

    # Add with swapped keys
    d[key2] = value1  # key2 now has key1's original value
    d[key1] = value2  # key1 now has key2's original value

    return d
