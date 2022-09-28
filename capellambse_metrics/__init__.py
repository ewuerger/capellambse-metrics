# SPDX-FileCopyrightText: Copyright capellambse-metrics contributors
# SPDX-License-Identifier: Apache-2.0

"""The capellambse_metrics package."""
import collections.abc as cabc
import pathlib
import typing as t
from importlib import metadata

import capellambse
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from capellambse.model import common, crosslayer

try:
    __version__ = metadata.version("capellambse_metrics")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"
del metadata


STYLESHEET_PATH = pathlib.Path(__file__).parent / "css" / "style.css"
NAVBAR_PATH = pathlib.Path(__file__).parent / "components" / "navbar.html"

TOPICS = (
    "activities",
    "functions",
    "capabilities",
    "interfaces",
    "classes",
    "components",
    "entities",
)
LAYERS = {
    "Operational Analysis": {
        "abbr": "oa",
        "topics": (
            top for top in TOPICS if top not in ("functions", "components")
        ),
        "xtype_id": "oa:OperationalAnalysis",
    },
    "System Analysis": {
        "abbr": "sa",
        "topics": (
            usual_topics := [
                top for top in TOPICS if top not in ("activities", "entities")
            ]
        ),
        "xtype_id": "ctx:SystemAnalysis",
    },
    "Logical Architecture": {
        "abbr": "la",
        "topics": usual_topics,
        "xtype_id": "la:LogicalArchitecture",
    },
    "Physical Architecture": {
        "abbr": "pa",
        "topics": usual_topics,
        "xtype_id": "pa:PhysicalArchitecture",
    },
}
TOPICS_BLACKLIST = {"pvmt", "diagrams"}


class Dashboard:
    title: str
    model: capellambse.MelodyModel
    earlier_model: capellambse.MelodyModel | None

    selected_layers: list[str] = []
    selected_objects: list[str] = []
    selected_chart_type: str = "Table"

    def __init__(
        self,
        model: capellambse.MelodyModel,
        earlier_model: capellambse.MelodyModel | None = None,
        title: str = "",
    ) -> None:
        self.title = title or f"{model.name} Metrics"
        self.model = model
        self.earlier_model = earlier_model

        self.chart_type_map = {
            "Table": st.dataframe,
            "Bar": self.render_topic_bar_chart,
            "Bubble": ...,
        }

        self.setup_style()
        self.setup_sidebar()
        self.render_main_page()

    def setup_style(self) -> None:
        st.markdown(
            f"<style>{STYLESHEET_PATH.read_text(encoding='utf-8')}<style/>",
            unsafe_allow_html=True,
        )
        st.markdown(
            NAVBAR_PATH.read_text(encoding="utf-8"), unsafe_allow_html=True
        )

    def setup_sidebar(self) -> None:
        st.sidebar.header("Filters:")
        st.sidebar.subheader("KPIs")
        self.selected_layers = st.sidebar.multiselect(
            "Select Architecture Layer(s):",
            options=LAYERS.keys(),
            default=LAYERS.keys(),
        )

        st.sidebar.markdown("---")

        options = [
            obj_name.split(":")[-1]
            for layers in common.XTYPE_HANDLERS.values()
            for obj_name in layers
        ]
        with st.sidebar.container():
            st.sidebar.subheader("Individual topics")
            self.selected_objects = st.sidebar.multiselect(
                "Select a ModelObject:",
                options=sorted(options),
                default=["LogicalFunction"],
            )
            self.selected_chart_type = st.sidebar.radio(
                "Select a chart type:", ("Table", "Bar", "Bubble")
            )  # type:ignore[assignment]

    def render_main_page(self) -> None:
        st.title(self.title)
        if self.earlier_model is not None:
            assert self.model.info.branch is not None
            assert self.model.info.rev_hash is not None
            now = self.model.info.branch + f" ({self.model.info.rev_hash[:7]})"
            assert self.earlier_model.info.branch is not None
            assert self.earlier_model.info.rev_hash is not None
            then = (
                self.earlier_model.info.branch
                + f" ({self.earlier_model.info.rev_hash[:7]})"
            )
            st.subheader(f"Comparison of {now} to {then}.")

        self.render_layer_sections(self.selected_layers, self.selected_objects)

    def render_layer_sections(
        self,
        selected_layers: cabc.Iterable[str],
        selected_objs: cabc.Iterable[str],
    ) -> None:
        layers = LAYERS
        for lhead in selected_layers:
            layer_info = layers[lhead]
            layer = getattr(
                self.model, layer_info["abbr"]  # type:ignore[index]
            )  # type:ignore[call-overload]
            earlier_layer = None
            if self.earlier_model is not None:
                earlier_layer = getattr(
                    self.earlier_model,
                    layer_info["abbr"],  # type:ignore[index]
                )

            self.render_kpi_section(
                lhead,
                layer_info,  # type:ignore[arg-type]
                layer,
                earlier_layer,
            )

            for obj_name in selected_objs:
                self.render_topic_section(
                    layer, obj_name, layer_info  # type: ignore[arg-type]
                )

            st.markdown("---")

    def render_kpi_section(
        self,
        layer_name: str,
        layer_info: cabc.Mapping[str, t.Any],
        layer: crosslayer.BaseArchitectureLayer,
        earlier_layer: crosslayer.BaseArchitectureLayer | None = None,
    ) -> None:
        st.header(f"{layer_name} Layer")
        if layer.description:
            st.markdown(layer.description, unsafe_allow_html=True)

        fig = self.render_kpi_pie_chart(layer_info, layer)
        st.plotly_chart(fig, use_container_width=True)

        for col, chead in zip(st.columns(5), layer_info["topics"]):
            findings = getattr(layer, f"all_{chead}")
            args = [chead.capitalize(), len(findings)]
            if earlier_layer is not None:
                earlier_findings = getattr(earlier_layer, f"all_{chead}")
                delta = args[-1] - len(earlier_findings)
                args.append(delta)
                if not delta:
                    args.append("off")

            with col:
                col.metric(
                    *args,
                    help=f"Total amount of {chead} found in {layer_name}.",
                )  # type: ignore[misc]

        self.render_requirements_kpi_section(layer, earlier_layer)

    def render_kpi_pie_chart(
        self,
        layer_info: cabc.Mapping[str, t.Any],
        layer: crosslayer.BaseArchitectureLayer,
    ) -> t.Any:
        layer_xtype = (
            f"org.polarsys.capella.core.data.{layer_info['xtype_id']}"
        )
        generics = {
            k: v
            for k, v in common.XTYPE_HANDLERS[None].items()
            if not k.endswith(("Architecture", "Analysis"))
        }
        obj_class_types = generics | common.XTYPE_HANDLERS[layer_xtype]
        data: dict[str, list[str | int]] = {"topic": [], "total": []}
        for cls_type in obj_class_types:
            if total := len(self.model.search(cls_type, below=layer)):
                data["topic"].append(cls_type.split(":")[-1])
                data["total"].append(total)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=data["topic"],
                    values=data["total"],
                    hole=0.3,
                    textinfo="percent+label",
                    insidetextorientation="horizontal",
                )
            ]
        )
        fig.update_traces(
            textposition="inside",
            textfont_size=20,
            marker=dict(line=dict(color="#000000", width=1.1)),
        )
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
        )
        return fig

    def render_requirements_kpi_section(
        self,
        layer: crosslayer.BaseArchitectureLayer,
        earlier_layer: crosslayer.BaseArchitectureLayer | None = None,
    ) -> None:
        requirement_types = self.model.search("RequirementType", below=layer)
        requirements = self.model.search("Requirement", below=layer)
        earlier_requirements: common.ElementList | list = []
        if earlier_layer is not None:
            assert self.earlier_model is not None
            earlier_requirements = self.earlier_model.search(
                "Requirement", below=earlier_layer
            )

        if not requirements and not earlier_requirements:
            return

        st.subheader("Requirements")
        all_req_types = set(requirement_types) | set(
            requirements.by_type  # type: ignore[arg-type]
        )
        num_req_type = len(all_req_types)
        for col, req_type in zip(st.columns(num_req_type), all_req_types):
            findings = requirements.by_type(req_type)
            label = "UNSET"
            if req_type is not None:
                label = req_type.long_name

            args = [label.capitalize(), len(findings)]
            if earlier_requirements:
                assert isinstance(earlier_requirements, common.ElementList)
                earlier_findings = earlier_requirements.by_type(req_type)
                delta = args[-1] - len(  # type:ignore[operator]
                    earlier_findings
                )
                args.append(delta)
                if not delta:
                    args.append("off")

            with col:
                col.metric(
                    *args,  # type:ignore[arg-type]
                    help=f"Total amount of requirements with type '{label}'.",
                )  # type: ignore[misc]

    def render_topic_section(
        self,
        layer: crosslayer.BaseArchitectureLayer,
        obj_name: str,
        layer_info: cabc.Mapping[str, t.Any],
    ) -> None:
        layer_xtype = (
            f"org.polarsys.capella.core.data.{layer_info['xtype_id']}"
        )
        base = common.XTYPE_HANDLERS[layer_xtype] | common.XTYPE_HANDLERS[None]
        if obj_name not in set(xt.split(":")[-1] for xt in base):
            return

        findings = self.model.search(obj_name, below=layer)
        st.header(obj_name)
        st.metric("Total", len(findings))
        # XXX: Need to pass list of UUIDs since ElementList isn't hashable
        data = get_topic_data([obj.uuid for obj in findings], self.model)
        self.chart_type_map[  # type: ignore[operator]
            self.selected_chart_type
        ](pd.DataFrame(data))

    def render_topic_bar_chart(self, df: pd.DataFrame) -> None:
        fig = px.bar(
            df,
            x="name",
            y=df.keys().drop("name"),
            labels={"x": "Name", "y": "Count"},
            height=600,
        )
        fig.update_layout(
            xaxis={"tickmode": "linear"},
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis={"showgrid": False},
            xaxis_title=None,
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)


@st.experimental_memo
def get_topic_data(
    findings: cabc.Sequence[str], _model: capellambse.MelodyModel
) -> list[dict[str, t.Any]]:
    topics_blacklist = TOPICS_BLACKLIST
    i = 0
    data = []
    num_findings = len(findings)
    progress_bar = st.progress(0)
    for uuid in findings:
        obj = _model.by_uuid(uuid)
        i += 1
        progress_bar.progress(i / num_findings)
        item = {"name": obj.name}
        for attr_name in dir(obj):
            if attr_name.startswith("_") or attr_name in topics_blacklist:
                continue

            attr = getattr(obj, attr_name)
            if not isinstance(attr, common.ElementList):
                continue

            item[attr_name] = len(attr)

        data.append(item)
    progress_bar.empty()
    return data


@st.experimental_singleton
def load_model(path: str, **kw) -> capellambse.MelodyModel:
    return capellambse.MelodyModel(path=path, **kw)
