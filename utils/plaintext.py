#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plaintext Processing Utility

@author: Hrishikesh Terdalkar
"""

import re
from typing import List

###############################################################################


class Tokenizer:
    """Regular-expressions-based Tokenizer

    To split a string using a regular expression, which matches
    either the tokens or the separators between tokens.

    Parameters
    ----------
    pattern : str
        The pattern used to build tokenizer
    gaps : bool, optional
        If True, the pattern is used to find separators between tokens.
        otherwise, the pattern is used to find the tokens themselves.
        The default is True.
    discard_empty : bool, optional
        If True, any empty tokens are discarded.
        The default is True.
    flags : int, optional
        Regexp flags used to compile the tokenizer pattern.
        The default is: re.UNICODE | re.MULTILINE | re.DOTALL
    """

    def __init__(
        self,
        pattern: str,
        gaps: bool = True,
        discard_empty: bool = True,
        flags=re.UNICODE | re.MULTILINE | re.DOTALL
    ):
        pattern = getattr(pattern, "pattern", pattern)
        self._pattern = pattern
        self._gaps = gaps
        self._discard_empty = discard_empty
        self._flags = flags
        self._regexp = re.compile(pattern, flags)

    def tokenize(self, text: str) -> List[str]:
        """Tokenize the given text

        Parameters
        ----------
        text : str
            Text to be tokenized

        Returns
        -------
        List[str]
            List of tokens
        """
        if self._gaps:
            if self._discard_empty:
                return [token for token in self._regexp.split(text) if token]
            else:
                return self._regexp.split(text)
        else:
            return self._regexp.findall(text)


###############################################################################