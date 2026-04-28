import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            :root {
                --bg: #071018;
                --panel: rgba(13, 30, 45, 0.72);
                --panel-strong: rgba(16, 43, 65, 0.86);
                --border: rgba(115, 214, 255, 0.20);
                --text: #e9f7ff;
                --muted: #8ba6b6;
                --cyan: #35d6ff;
                --blue: #2878ff;
                --teal: #19d3a2;
                --red: #ff4b66;
                --amber: #ffc857;
            }

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            .stApp {
                background:
                    radial-gradient(circle at 15% 10%, rgba(40, 120, 255, 0.22), transparent 28%),
                    radial-gradient(circle at 80% 4%, rgba(25, 211, 162, 0.14), transparent 25%),
                    linear-gradient(135deg, #050b11 0%, #071018 42%, #0a1720 100%);
                color: var(--text);
            }

            section[data-testid="stSidebar"] {
                background: rgba(5, 14, 22, 0.96);
                border-right: 1px solid var(--border);
            }

            section[data-testid="stSidebar"] * {
                color: var(--text);
            }

            .block-container {
                padding-top: 1.45rem;
                padding-bottom: 1rem;
            }

            .hero {
                position: relative;
                overflow: hidden;
                padding: 3rem 2.4rem;
                border: 1px solid var(--border);
                border-radius: 24px;
                background:
                    linear-gradient(125deg, rgba(9, 24, 36, 0.95), rgba(13, 43, 64, 0.78)),
                    url("https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1600&q=80");
                background-size: cover;
                background-position: center;
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
                isolation: isolate;
                animation: heroReveal 900ms ease both;
            }

            .hero::before {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(90deg, rgba(5, 12, 18, 0.92), rgba(5, 12, 18, 0.44));
                z-index: -1;
            }

            .hero::after {
                content: "";
                position: absolute;
                left: -35%;
                top: 0;
                width: 34%;
                height: 100%;
                background: linear-gradient(
                    105deg,
                    transparent,
                    rgba(53, 214, 255, 0.12),
                    rgba(255, 255, 255, 0.10),
                    transparent
                );
                transform: skewX(-18deg);
                animation: heroScan 6.5s ease-in-out infinite;
                pointer-events: none;
            }

            .hero-eyebrow {
                color: var(--cyan);
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-size: 0.8rem;
                margin-bottom: 0.7rem;
            }

            .hero h1 {
                max-width: 900px;
                color: #ffffff;
                font-size: clamp(2.35rem, 6vw, 5.1rem);
                line-height: 1;
                margin: 0 0 1rem 0;
                font-weight: 800;
                letter-spacing: 0;
                animation: titleRise 800ms ease 120ms both;
            }

            .hero p {
                max-width: 780px;
                color: #b7d6e5;
                font-size: 1.08rem;
                line-height: 1.7;
                margin: 0;
                animation: titleRise 850ms ease 220ms both;
            }

            .hero-meta {
                display: flex;
                gap: 0.8rem;
                flex-wrap: wrap;
                margin-top: 1.6rem;
            }

            .scanline-panel {
                position: relative;
                margin-top: 1.6rem;
                max-width: 640px;
                height: 62px;
                border: 1px solid rgba(53, 214, 255, 0.22);
                border-radius: 16px;
                background:
                    linear-gradient(90deg, rgba(53, 214, 255, 0.05) 1px, transparent 1px),
                    linear-gradient(rgba(53, 214, 255, 0.04) 1px, transparent 1px),
                    rgba(3, 15, 24, 0.48);
                background-size: 38px 38px, 38px 38px, auto;
                overflow: hidden;
            }

            .scanline-panel::before {
                content: "";
                position: absolute;
                left: -20%;
                top: 0;
                width: 20%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(53, 214, 255, 0.3), transparent);
                animation: networkSweep 3.2s linear infinite;
            }

            .scan-dot {
                position: absolute;
                width: 9px;
                height: 9px;
                border-radius: 999px;
                background: #35d6ff;
                box-shadow: 0 0 18px rgba(53, 214, 255, 0.9);
                animation: dotPulse 1.7s ease-in-out infinite;
            }

            .scan-dot:nth-child(1) { left: 12%; top: 45%; animation-delay: 0s; }
            .scan-dot:nth-child(2) { left: 39%; top: 24%; animation-delay: 0.35s; }
            .scan-dot:nth-child(3) { left: 62%; top: 58%; animation-delay: 0.7s; }
            .scan-dot:nth-child(4) { left: 84%; top: 34%; animation-delay: 1.05s; }

            .hero-chip, .pill {
                border: 1px solid rgba(53, 214, 255, 0.28);
                background: rgba(5, 18, 28, 0.62);
                border-radius: 999px;
                padding: 0.52rem 0.82rem;
                color: #dcf8ff;
                font-size: 0.88rem;
                animation: chipFloat 4.5s ease-in-out infinite;
            }

            .section-title {
                margin: 1.8rem 0 0.45rem 0;
                color: #ffffff;
                font-size: 1.42rem;
                font-weight: 800;
            }

            .section-subtitle {
                color: var(--muted);
                margin-top: 0;
                margin-bottom: 1rem;
            }

            .glass-card {
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 1.25rem;
                background: linear-gradient(145deg, rgba(15, 36, 54, 0.78), rgba(9, 20, 31, 0.72));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.25);
                backdrop-filter: blur(18px);
                margin-bottom: 1rem;
                animation: cardIn 520ms ease both;
                transition: transform 220ms ease, border-color 220ms ease, box-shadow 220ms ease;
            }

            .glass-card:hover {
                transform: translateY(-3px);
                border-color: rgba(53, 214, 255, 0.38);
                box-shadow: 0 24px 65px rgba(0, 0, 0, 0.3), 0 0 32px rgba(53, 214, 255, 0.08);
            }

            .kpi-card {
                position: relative;
                overflow: hidden;
                min-height: 148px;
                border: 1px solid rgba(53, 214, 255, 0.24);
                border-radius: 18px;
                padding: 1.25rem;
                background: linear-gradient(150deg, rgba(12, 34, 52, 0.92), rgba(8, 18, 29, 0.9));
                box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28), 0 0 28px rgba(53, 214, 255, 0.08);
                animation: floatCard 4s ease-in-out infinite;
                margin-bottom: 1rem;
                transition: transform 220ms ease, border-color 220ms ease, box-shadow 220ms ease;
            }

            .kpi-card:hover {
                transform: translateY(-7px) scale(1.01);
                border-color: rgba(53, 214, 255, 0.52);
                box-shadow: 0 24px 70px rgba(0, 0, 0, 0.32), 0 0 44px rgba(53, 214, 255, 0.16);
            }

            .kpi-card::after {
                content: "";
                position: absolute;
                inset: -60% auto auto -20%;
                width: 190px;
                height: 190px;
                background: radial-gradient(circle, rgba(53, 214, 255, 0.23), transparent 62%);
                animation: pulseGlow 3.2s ease-in-out infinite;
            }

            .kpi-label {
                color: var(--muted);
                font-size: 0.9rem;
                font-weight: 700;
                margin-bottom: 0.7rem;
            }

            .kpi-value {
                color: #ffffff;
                font-size: 2.15rem;
                font-weight: 800;
                line-height: 1;
                animation: valuePop 700ms ease both;
            }

            .kpi-unit {
                color: var(--cyan);
                font-size: 0.92rem;
                font-weight: 700;
                margin-top: 0.35rem;
            }

            .kpi-trend {
                color: var(--teal);
                font-size: 0.86rem;
                margin-top: 0.9rem;
            }

            .status-safe, .status-danger, .status-warning {
                border-radius: 16px;
                padding: 1rem 1.15rem;
                font-weight: 700;
                border: 1px solid transparent;
                margin-bottom: 0.8rem;
                animation: statusSlide 460ms ease both;
            }

            .status-safe {
                color: #cffff1;
                background: rgba(25, 211, 162, 0.14);
                border-color: rgba(25, 211, 162, 0.38);
                box-shadow: 0 0 22px rgba(25, 211, 162, 0.08);
            }

            .status-danger {
                color: #ffe3e8;
                background: rgba(255, 75, 102, 0.15);
                border-color: rgba(255, 75, 102, 0.44);
                animation: statusSlide 460ms ease both, dangerPulse 1.6s ease-in-out infinite;
            }

            .status-warning {
                color: #fff2ca;
                background: rgba(255, 200, 87, 0.14);
                border-color: rgba(255, 200, 87, 0.38);
            }

            .gauge {
                border-radius: 999px;
                height: 13px;
                background: rgba(255, 255, 255, 0.08);
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }

            .gauge-fill {
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, #19d3a2, #35d6ff, #2878ff);
                box-shadow: 0 0 24px rgba(53, 214, 255, 0.35);
                animation: gaugeFill 900ms ease both, waterMove 2.2s linear infinite;
                background-size: 180% 100%;
            }

            .mini-label {
                color: #9bb6c7;
                font-size: 0.82rem;
                margin-bottom: 0.35rem;
            }

            .stButton > button {
                width: 100%;
                border: 1px solid rgba(53, 214, 255, 0.42);
                border-radius: 14px;
                background: linear-gradient(135deg, #1e8bff, #35d6ff);
                color: #021019;
                font-weight: 800;
                padding: 0.72rem 1rem;
                box-shadow: 0 12px 28px rgba(40, 120, 255, 0.22);
                transition: transform 180ms ease, box-shadow 180ms ease;
                position: relative;
                overflow: hidden;
            }

            .stButton > button::after {
                content: "";
                position: absolute;
                inset: 0 auto 0 -45%;
                width: 42%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.28), transparent);
                transform: skewX(-18deg);
                transition: left 380ms ease;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 16px 38px rgba(53, 214, 255, 0.28);
                color: #021019;
            }

            .stButton > button:hover::after {
                left: 120%;
            }

            div[data-testid="stDataFrame"] {
                animation: cardIn 580ms ease both;
            }

            div[data-testid="stPlotlyChart"] {
                animation: chartGlow 900ms ease both;
            }

            div[data-baseweb="input"], div[data-baseweb="select"] {
                border-radius: 14px;
            }

            .footer {
                color: #84a4b5;
                text-align: center;
                padding: 2rem 0 0.5rem;
                font-size: 0.9rem;
            }

            @keyframes pulseGlow {
                0%, 100% { opacity: 0.45; transform: scale(1); }
                50% { opacity: 0.95; transform: scale(1.16); }
            }

            @keyframes floatCard {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-4px); }
            }

            @keyframes heroReveal {
                from { opacity: 0; transform: translateY(16px) scale(0.992); filter: blur(8px); }
                to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
            }

            @keyframes heroScan {
                0%, 45% { left: -38%; opacity: 0; }
                55% { opacity: 1; }
                100% { left: 125%; opacity: 0; }
            }

            @keyframes titleRise {
                from { opacity: 0; transform: translateY(18px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes chipFloat {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-3px); }
            }

            @keyframes cardIn {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes valuePop {
                from { opacity: 0; transform: translateY(8px) scale(0.96); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }

            @keyframes statusSlide {
                from { opacity: 0; transform: translateX(-10px); }
                to { opacity: 1; transform: translateX(0); }
            }

            @keyframes dangerPulse {
                0%, 100% { box-shadow: 0 0 18px rgba(255, 75, 102, 0.08); }
                50% { box-shadow: 0 0 34px rgba(255, 75, 102, 0.24); }
            }

            @keyframes gaugeFill {
                from { width: 0; }
            }

            @keyframes waterMove {
                from { background-position: 0% 50%; }
                to { background-position: 180% 50%; }
            }

            @keyframes chartGlow {
                from { opacity: 0; filter: drop-shadow(0 0 0 rgba(53, 214, 255, 0)); }
                to { opacity: 1; filter: drop-shadow(0 0 14px rgba(53, 214, 255, 0.08)); }
            }

            @keyframes networkSweep {
                from { left: -22%; }
                to { left: 122%; }
            }

            @keyframes dotPulse {
                0%, 100% { transform: scale(1); opacity: 0.72; }
                50% { transform: scale(1.55); opacity: 1; }
            }

            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    animation-duration: 0.001ms !important;
                    animation-iteration-count: 1 !important;
                    scroll-behavior: auto !important;
                    transition-duration: 0.001ms !important;
                }
            }

            @media (max-width: 768px) {
                .hero { padding: 2.2rem 1.25rem; border-radius: 18px; }
                .kpi-card { min-height: 130px; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
