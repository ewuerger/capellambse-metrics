# SPDX-FileCopyrightText: Copyright capellambse-metrics contributors
# SPDX-License-Identifier: Apache-2.0
import pathlib

import streamlit as st
import yaml

from capellambse_metrics import Dashboard, load_model

CONFIG_PATH = pathlib.Path(__file__).parents[1] / "config.yaml"


if __name__ == "__main__":
    st.set_page_config(
        page_title="Capellambse Metrics",
        page_icon=":bullettrain_side:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    model = load_model(**config["model"])
    earlier_model = config.get("earlier_model_revision")
    if earlier_model is not None:
        config["model"]["revision"] = earlier_model
        earlier_model = load_model(**config["model"])

    Dashboard(model, earlier_model=earlier_model)
