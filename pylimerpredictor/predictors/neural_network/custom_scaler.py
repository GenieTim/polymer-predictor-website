from typing import List, Union

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler
from torch import Tensor


class CustomScaler(BaseEstimator, TransformerMixin):
    """
    A custom scaler that handles both binary and continuous variables.

    This scaler applies StandardScaler to continuous variables while leaving
    binary variables unchanged. It returns the feature matrix with binary
    columns ordered first.

    Attributes:
        scaler (StandardScaler): The StandardScaler instance for continuous variables.
        bin_vars_index (List[int]): Indices of binary variables.
        cont_vars_index (Union[List[int], None]): Indices of continuous variables.
    """

    def __init__(
        self,
        bin_vars_index: List[int],
        cont_vars_index: Union[List[int], None] = None,
        copy: bool = True,
        with_mean: bool = True,
        with_std: bool = True,
        log_y: bool = False,
    ):
        """
        Initialize the CustomScaler.

        Args:
            bin_vars_index (List[int]): Indices of binary variables.
            cont_vars_index (Union[List[int], None], optional): Indices of continuous variables.
                If None, it will be inferred during fitting. Defaults to None.
            copy (bool, optional): If True, a copy of the input data is made. Defaults to True.
            with_mean (bool, optional): If True, center the data before scaling. Defaults to True.
            with_std (bool, optional): If True, scale the data to unit variance. Defaults to True.
        """
        self.scaler = StandardScaler(copy=copy, with_mean=with_mean, with_std=with_std)
        self.bin_vars_index = bin_vars_index
        self.cont_vars_index = cont_vars_index
        self.log_y = log_y

    def fit(self, X, y=None):
        """
        Fit the scaler to the data.

        If cont_vars_index is not provided, it will be inferred as all columns
        not in bin_vars_index.

        Args:
            X (array-like): The input samples to fit the scaler.
            y (array-like, optional): Ignored. Kept for compatibility with sklearn API.

        Returns:
            self: The fitted scaler.
        """
        if self.log_y and y is not None:
            y = np.log(y)
        if self.cont_vars_index is None:
            # just take all columns that are not in bin_vars_index
            self.cont_vars_index = list(
                set(range(X.shape[1])) - set(self.bin_vars_index)
            )
        self.scaler.fit(X[:, self.cont_vars_index], y)
        return self

    def transform(self, X, y=None, copy: Union[bool, None] = None):
        """
        Transform the data using the fitted scaler.

        Applies the StandardScaler transformation to continuous variables and
        concatenates them with the unchanged binary variables.

        Args:
            X (array-like): The input samples to transform.
            y (array-like, optional): Ignored. Kept for compatibility with sklearn API.
            copy (Union[bool, None], optional): If True, a copy of X will be created.
                If None, uses the copy parameter passed in __init__. Defaults to None.

        Returns:
            np.ndarray: The transformed data with binary columns first.

        Raises:
            AssertionError: If cont_vars_index is not set during fit.
        """
        if self.log_y and y is not None:
            y = np.log(y)
        assert self.cont_vars_index is not None, "Cont_vars_index not set during fit"
        if isinstance(X, list):
            X = np.array(X)

        # Ensure X is numeric
        X = np.asarray(X, dtype=np.float64)

        X_tail = self.scaler.transform(X[:, self.cont_vars_index], copy=copy)

        # Handle empty bin_vars_index case
        if len(self.bin_vars_index) == 0:
            return X_tail

        # Ensure consistent dtypes
        X_bin = X[:, self.bin_vars_index].astype(X_tail.dtype)
        result = np.concatenate((X_bin, X_tail), axis=1)

        # Ensure result is float type
        return result.astype(np.float64)

    def inverse_transform(self, X, copy: Union[bool, None] = None):
        """
        Inverse transform the data using the fitted scaler.

        Applies the inverse StandardScaler transformation to continuous variables and
        concatenates them with the unchanged binary variables.

        Args:
            X (array-like): The input samples to inverse transform.
            copy (Union[bool, None], optional): If True, a copy of X will be created.
                If None, uses the copy parameter passed in __init__. Defaults to None.

        Returns:
            np.ndarray: The inverse transformed data with binary columns first.

        Raises:
            AssertionError: If cont_vars_index is not set during fit.
        """
        assert self.cont_vars_index is not None, "Cont_vars_index not set during fit"

        # Ensure X is numeric
        X = np.asarray(X, dtype=np.float64)

        X_tail = self.scaler.inverse_transform(
            X[:, len(self.bin_vars_index) :], copy=copy
        )

        # Handle empty bin_vars_index case
        if len(self.bin_vars_index) == 0:
            return X_tail

        # Get binary columns (first len(self.bin_vars_index) columns)
        X_bin = X[:, : len(self.bin_vars_index)].astype(X_tail.dtype)
        result = np.concatenate((X_bin, X_tail), axis=1)

        # Ensure result is float type
        return result.astype(np.float64)


class TargetScaler(BaseEstimator, TransformerMixin):
    """
    A custom scaler that applies log to one set of target variables and log1p to another set,
    followed by StandardScaler, with the option to exclude certain variables from scaling.
    """

    def __init__(
        self,
        log_vars_index: List[int] = [],
        log1p_vars_index: List[int] = [],
        exclude_vars_index: List[int] = [],
        copy: bool = True,
        with_mean: bool = True,
        with_std: bool = True,
    ):
        self.log_vars_index = log_vars_index
        self.log1p_vars_index = log1p_vars_index
        self.exclude_vars_index = exclude_vars_index
        self.scaler = StandardScaler(copy=copy, with_mean=with_mean, with_std=with_std)

    def fit(self, X, y=None):
        """
        Fit the scaler to the data.

        Args:
            X (array-like): The input samples.
            y (array-like, optional): Ignored. Kept for compatibility with sklearn API.

        Returns:
            self: The fitted scaler.
        """
        X_transformed = X.copy()
        X_transformed[:, self.log_vars_index] = np.log(
            X_transformed[:, self.log_vars_index]
        )
        X_transformed[:, self.log1p_vars_index] = np.log1p(
            X_transformed[:, self.log1p_vars_index]
        )

        # Exclude specified variables from scaling
        scale_vars = list(set(range(X.shape[1])) - set(self.exclude_vars_index))
        self.scaler.fit(X_transformed[:, scale_vars])
        return self

    def transform(self, X, copy: bool = True):
        """
        Apply log and log1p transformations to the respective target variables,
        and scale the non-excluded variables.

        Args:
            X (array-like): The input samples to transform.

        Returns:
            np.ndarray: The transformed data.
        """
        if copy:
            if isinstance(X, Tensor):
                X_transformed = X.numpy().copy()
            else:
                X_transformed = X.copy()
        else:
            X_transformed = X

        X_transformed[:, self.log_vars_index] = np.log(
            X_transformed[:, self.log_vars_index]
        )
        X_transformed[:, self.log1p_vars_index] = np.log1p(
            X_transformed[:, self.log1p_vars_index]
        )

        # Scale only non-excluded variables
        scale_vars = list(set(range(X.shape[1])) - set(self.exclude_vars_index))
        X_transformed[:, scale_vars] = self.scaler.transform(
            X_transformed[:, scale_vars]
        )
        return X_transformed

    def inverse_transform(self, X, copy: bool = True):
        """
        Apply exp and expm1 to reverse the log and log1p transformations on the respective target variables,
        and inverse scale the non-excluded variables.

        Args:
            X (array-like): The input samples to inverse transform.

        Returns:
            np.ndarray: The inverse transformed data.
        """
        if copy:
            if isinstance(X, Tensor):
                X_inv = X.numpy().copy()
            else:
                X_inv = X.copy()
        else:
            X_inv = X

        # Inverse scale only non-excluded variables
        scale_vars = list(set(range(X.shape[1])) - set(self.exclude_vars_index))
        X_inv[:, scale_vars] = self.scaler.inverse_transform(X_inv[:, scale_vars])

        X_inv[:, self.log_vars_index] = np.exp(X_inv[:, self.log_vars_index])
        X_inv[:, self.log1p_vars_index] = np.expm1(X_inv[:, self.log1p_vars_index])
        return X_inv
