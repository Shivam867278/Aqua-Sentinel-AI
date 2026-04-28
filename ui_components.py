from typing import Any

import streamlit as st


def hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-eyebrow">AI Water Intelligence Platform</div>
            <h1>Aqua Sentinel AI</h1>
            <p>
                Premium industrial dashboard for leakage detection, water quality intelligence,
                demand forecasting, asset health, and live operations across smart water networks.
            </p>
            <div class="hero-meta">
                <span class="hero-chip">💧 Live IoT telemetry</span>
                <span class="hero-chip">🧠 AI assisted decisions</span>
                <span class="hero-chip">🛡️ Risk-aware operations</span>
                <span class="hero-chip">📈 Predictive demand planning</span>
            </div>
            <div class="scanline-panel" aria-hidden="true">
                <span class="scan-dot"></span>
                <span class="scan-dot"></span>
                <span class="scan-dot"></span>
                <span class="scan-dot"></span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: Any, unit: str, trend: str, icon: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{icon} {label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-unit">{unit}</div>
            <div class="kpi-trend">{trend}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status(message: str, state: str = "safe") -> None:
    css_class = {
        "safe": "status-safe",
        "danger": "status-danger",
        "warning": "status-warning",
    }.get(state, "status-warning")
    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def gauge(label: str, value: float, suffix: str = "%") -> None:
    clipped = max(0, min(100, value))
    st.markdown(
        f"""
        <div class="mini-label">{label}: <b>{clipped:.1f}{suffix}</b></div>
        <div class="gauge"><div class="gauge-fill" style="width:{clipped:.1f}%"></div></div>
        """,
        unsafe_allow_html=True,
    )


def glass_start() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)


def glass_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)
