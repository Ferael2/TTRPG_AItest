import streamlit as st


def inject_styles():
	"""Apply responsive layout styles for desktop and phone-sized screens."""
	st.markdown(
		"""
		<style>
		section[data-testid="stMain"] .block-container {
			width: 100%;
			max-width: 100%;
			padding-left: clamp(0.75rem, 3vw, 2rem);
			padding-right: clamp(0.75rem, 3vw, 2rem);
		}

		.auth-portal-card {
			width: 100%;
			box-sizing: border-box;
		}

		@media (max-width: 640px) {
			section[data-testid="stMain"] .block-container {
				padding: 0.75rem 0.5rem 4rem;
			}

			.auth-portal-title {
				font-size: clamp(1.5rem, 8vw, 2.4rem);
				line-height: 1.2;
				overflow-wrap: normal;
				word-break: normal;
			}

			div[data-testid="stHorizontalBlock"] {
				gap: 0.5rem;
			}

			div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
				min-width: 0;
			}

			div[data-testid="stHorizontalBlock"]:has(.responsive-wrapper),
			div[data-testid="stHorizontalBlock"]:has(.auth-portal-card) {
				gap: 0;
			}

			div[data-testid="stHorizontalBlock"]:has(.responsive-wrapper) > div[data-testid="column"]:first-child,
			div[data-testid="stHorizontalBlock"]:has(.responsive-wrapper) > div[data-testid="column"]:last-child,
			div[data-testid="stHorizontalBlock"]:has(.auth-portal-card) > div[data-testid="column"]:first-child,
			div[data-testid="stHorizontalBlock"]:has(.auth-portal-card) > div[data-testid="column"]:last-child {
				display: none;
			}

			div[data-testid="stHorizontalBlock"]:has(.responsive-wrapper) > div[data-testid="column"],
			div[data-testid="stHorizontalBlock"]:has(.auth-portal-card) > div[data-testid="column"] {
				width: 100% !important;
				flex: 1 1 100%;
			}
		}
		</style>
		""",
		unsafe_allow_html=True,
	)