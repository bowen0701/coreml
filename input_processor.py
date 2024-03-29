#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function

from typing import Dict, OrderedDict, Tuple
from classes import dataclass
from collections import OrderedDict
from copy import deepcopy

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch import Tensor

from data_loader import DataReader, InputData


@dataclass
class InputPreprocData:
    float_features: np.ndarray
    id_list_features: np.ndarray
    id_score_list_features: np.ndarray
    embedding_features: np.ndarray
    labels: np.ndarray


class InputPreproc:
    def __init__(
        self,
        data_reader: DataReader,
        is_train: bool = True,
    ) -> None:
        self.data_reader = data_reader
        self.is_train = is_train
        self.id_list_features_metadata = None

    def __call__(
        self,
        input_data: InputData,
    ) -> InputPreprocData:
        labels_df = input_data.labels
        
        features_df = input_data.features
        (
            float_features_np,
            id_list_features_np,
            id_score_list_features_np,
            embedding_features_np,
        ) = self.get_feature_groups_data(features_df)

        # Preprocess id_list features.
        if self.is_train:
            self.id_list_features_metadata = self.get_id_list_features_metadata(
                id_list_features_np
            )

        id_list_features_preproc_np = self.id_list_features_preproc(
            id_list_features_np
        )
        
        # Preprocess id_score_list features.
        id_score_list_features_preproc_np = self.id_score_list_features_preproc(
            id_score_list_features_np
        )

        return InputPreprocData(
            float_features=float_features_np,
            id_list_features=id_list_features_preproc_np,
            id_score_list_features=id_score_list_features_preproc_np,
            embedding_features=embedding_features_np,
            labels=labels_df.values
        )

    def get_feature_groups_data(
        self,
        features_df: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        float_features_np = (
            features_df.loc[:, self.data_reader.float_feature_names]
        ).values
        id_list_features_np = (
            features_df.loc[:, self.data_reader.id_list_feature_names]
        ).values
        id_score_list_features_np = (
            features_df.loc[:, self.data_reader.id_score_list_feature_names]
        ).values
        embedding_features_np = (
            features_df.loc[:, self.data_reader.embedding_feature_names]
        ).values
        return (
            float_features_np,
            id_list_features_np,
            id_score_list_features_np,
            embedding_features_np,
        )

    def get_id_list_features_metadata(
        self,
        id_list_examples_np: np.ndarray,
    ) -> Dict[str, Dict[str, int]]:
        id_list_features_metadata = OrderedDict()

        for c in range(id_list_examples_np.shape[1]):
            col = id_list_examples_np[:, c]
            unique_data = np.unique(col)
            data_idx_map = {data: idx for idx, data in enumerate(unique_data)}
            id_list_features_metadata[
                self.data_reader.id_list_feature_names[c]
            ] = data_idx_map
        
        return id_list_features_metadata
    
    def id_list_features_preproc(
        self,
        id_list_features_np: np.ndarray,
    ) -> np.ndarray:
        id_list_features_preproc_np = deepcopy(id_list_features_np)

        for c in range(id_list_features_preproc_np.shape[1]):
            # Convert category data to idx, with unknown category mapping to largest idx + 1.
            # Note: The unknown category would only appear in the test data.
            data_idx_map = self.id_list_features_metadata[
                self.data_reader.id_list_feature_names[c]
            ]
            data2idx = lambda x: data_idx_map.get(x, len(data_idx_map))
            result = np.array(list(map(data2idx, id_list_features_preproc_np[:, c])))
            id_list_features_preproc_np[:, c] = result
        
        return id_list_features_preproc_np.astype(np.int64)
    
    def id_score_list_features_preproc(
        self,
        id_score_list_features_np: np.ndarray,
    ) -> np.ndarray:
        id_score_list_features_preproc_np = deepcopy(id_score_list_features_np)
        return id_score_list_features_preproc_np.astype(np.float64)
