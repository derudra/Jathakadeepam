from datetime import date, time, datetime
from zoneinfo import ZoneInfo

import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from prokerala_api import ApiClient


# ---------------------------------------------------------
# APP CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="JathakaDeepam",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 50% -15%,
                rgba(193, 154, 86, 0.14),
                transparent 32%
            ),
            #0c0c0e;
        color: #f3efe6;
    }

    .block-container {
        max-width: 760px;
        padding-top: 3.5rem;
        padding-bottom: 6rem;
    }

    .jd-symbol {
        text-align: center;
        font-size: 2rem;
        color: #c6a66a;
        margin-bottom: 0.4rem;
    }

    .jd-eyebrow {
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.23em;
        font-size: 0.68rem;
        color: #a99065;
        margin-bottom: 0.8rem;
    }

    .jd-title {
        text-align: center;
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 400;
        font-size: 3.2rem;
        line-height: 1;
        color: #f4ead7;
        margin: 0;
    }

    .jd-malayalam {
        text-align: center;
        font-size: 1.08rem;
        color: #cabc9e;
        margin-top: 0.75rem;
    }

    .jd-subtitle {
        max-width: 520px;
        margin: 0.8rem auto 2.6rem auto;
        text-align: center;
        color: #858078;
        line-height: 1.5;
        font-size: 0.92rem;
    }

    div[data-testid="stForm"] {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(198,166,106,0.18);
        border-radius: 20px;
        padding: 1.3rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(198,166,106,0.12);
        border-radius: 14px;
        padding: 0.8rem;
    }

    .jd-success {
        margin-top: 1.5rem;
        padding: 1.15rem 1.3rem;
        border: 1px solid rgba(198,166,106,0.18);
        border-radius: 16px;
        background: rgba(198,166,106,0.05);
    }

    .jd-success-title {
        color: #d8bd87;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .jd-muted {
        color: #88827a;
        font-size: .88rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

@st.cache_resource
def get_timezone_finder():
    return TimezoneFinder()


@st.cache_resource
def get_geocoder():
    return Nominatim(
        user_agent="jathakadeepam-astrology-app"
    )


@st.cache_resource
def get_prokerala_client():
    try:
        client_id = st.secrets["PROKERALA_CLIENT_ID"]
        client_secret = st.secrets["PROKERALA_CLIENT_SECRET"]
    except KeyError:
        raise RuntimeError(
            "Prokerala credentials are missing from Streamlit Secrets."
        )

    return ApiClient(
        client_id,
        client_secret
    )


@st.cache_data(ttl=86400)
def resolve_birthplace(place):
    """
    Converts a place name into latitude, longitude,
    timezone, and formatted address.
    """

    geocoder = get_geocoder()

    location = geocoder.geocode(
        place,
        exactly_one=True,
        addressdetails=True,
        timeout=10,
    )

    if location is None:
        raise ValueError(
            "Place not found. Try something more specific, "
            "for example: Kozhikode, Kerala, India."
        )

    latitude = float(location.latitude)
    longitude = float(location.longitude)

    timezone_finder = get_timezone_finder()

    timezone_name = timezone_finder.timezone_at(
        lat=latitude,
        lng=longitude,
    )

    if not timezone_name:
        raise ValueError(
            "Timezone could not be determined for this place."
        )

    return {
        "name": location.address,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone_name,
    }


def create_birth_datetime(
    birth_date,
    birth_time,
    timezone_name
):
    """
    Creates an ISO-8601 datetime with the correct timezone offset.
    """

    timezone = ZoneInfo(timezone_name)

    birth_datetime = datetime.combine(
        birth_date,
        birth_time
    )

    birth_datetime = birth_datetime.replace(
        tzinfo=timezone
    )

    return birth_datetime.isoformat()


def get_astrology_data(
    birth_datetime,
    latitude,
    longitude
):
    """
    Gets Basic Kundli + Planet Position.

    Prokerala is deliberately queried in English.
    Later Gemini can handle Malayalam/Hindi/English interpretation.
    """

    client = get_prokerala_client()

    params = {
        "ayanamsa": 1,  # Lahiri
        "coordinates": f"{latitude},{longitude}",
        "datetime": birth_datetime,
        "la": "en",
    }

    kundli = client.get(
        "v2/astrology/kundli",
        params
    )

    planet_positions = client.get(
        "v2/astrology/planet-position",
        params
    )

    return {
        "kundli": kundli,
        "planet_positions": planet_positions,
    }


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "astrology_data" not in st.session_state:
    st.session_state.astrology_data = None

if "birth_profile" not in st.session_state:
    st.session_state.birth_profile = None


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="jd-symbol">✦</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="jd-eyebrow">'
    'Vedic Astrology · AI Consultation'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="jd-title">JathakaDeepam</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="jd-malayalam">ജാതകദീപം</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="jd-subtitle">
        Enter your birth details to create your
        Vedic horoscope.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# FORM
# ---------------------------------------------------------

with st.form("birth_details_form"):

    name = st.text_input(
        "Name",
        placeholder="Your name",
    )

    birthplace = st.text_input(
        "Place of birth",
        placeholder="Kozhikode, Kerala, India",
        help=(
            "Enter town/city + state/country "
            "for the most accurate location."
        ),
    )

    col1, col2 = st.columns(2)

    with col1:
        birth_date = st.date_input(
            "Date of birth",
            value=date(1995, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )

    with col2:
        birth_time = st.time_input(
            "Time of birth",
            value=time(6, 0),
        )

    col3, col4 = st.columns(2)

    with col3:
        language = st.selectbox(
            "Consultation language",
            [
                "മലയാളം",
                "English",
                "हिन्दी",
            ],
        )

    with col4:
        chart_style = st.selectbox(
            "Chart style",
            [
                "Kerala",
                "South Indian",
                "North Indian",
            ],
        )

    st.caption(
        "Calculation method: Vedic Sidereal · "
        "Lahiri Ayanamsa"
    )

    generate = st.form_submit_button(
        "Generate Jathakam →",
        use_container_width=True,
    )


# ---------------------------------------------------------
# GENERATE HOROSCOPE
# ---------------------------------------------------------

if generate:

    if not birthplace.strip():
        st.error(
            "Please enter your place of birth."
        )
        st.stop()

    try:

        with st.status(
            "Preparing your Jathakam…",
            expanded=True
        ) as status:

            st.write(
                "Finding birthplace coordinates…"
            )

            location = resolve_birthplace(
                birthplace.strip()
            )

            st.write(
                f"Found **{location['name']}**"
            )

            st.write(
                "Determining local timezone…"
            )

            iso_datetime = create_birth_datetime(
                birth_date,
                birth_time,
                location["timezone"],
            )

            st.write(
                f"Timezone: **{location['timezone']}**"
            )

            st.write(
                "Calculating Vedic horoscope…"
            )

            astrology_data = get_astrology_data(
                iso_datetime,
                location["latitude"],
                location["longitude"],
            )

            st.session_state.astrology_data = (
                astrology_data
            )

            st.session_state.birth_profile = {
                "name": name.strip(),
                "date": str(birth_date),
                "time": str(birth_time),
                "place": location["name"],
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "timezone": location["timezone"],
                "datetime": iso_datetime,
                "language": language,
                "chart_style": chart_style,
                "ayanamsa": "Lahiri",
            }

            status.update(
                label="Jathakam calculated",
                state="complete",
                expanded=False,
            )

    except Exception as error:

        st.error(
            "JathakaDeepam couldn't generate "
            "the horoscope."
        )

        st.exception(error)


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

if st.session_state.astrology_data:

    data = st.session_state.astrology_data
    profile = st.session_state.birth_profile

    st.divider()

    st.markdown(
        "## Your Jathakam"
    )

    if profile["name"]:
        st.write(
            f"**{profile['name']}**"
        )

    st.caption(
        profile["place"]
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Timezone",
        profile["timezone"],
    )

    metric2.metric(
        "Latitude",
        f"{profile['latitude']:.4f}",
    )

    metric3.metric(
        "Longitude",
        f"{profile['longitude']:.4f}",
    )

    st.markdown(
        """
        <div class="jd-success">
            <div class="jd-success-title">
                Horoscope calculation received ✓
            </div>

            <div class="jd-muted">
                Sidereal Vedic calculation using
                Lahiri Ayanamsa. Raw astrology data is
                temporarily visible so the calculation
                can be verified before AI interpretation
                is enabled.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    tab1, tab2, tab3 = st.tabs(
        [
            "Birth Profile",
            "Kundli Data",
            "Planet Positions",
        ]
    )

    with tab1:
        st.json(profile)

    with tab2:
        st.json(
            data["kundli"]
        )

    with tab3:
        st.json(
            data["planet_positions"]
        )

    st.info(
        "Compare these results with one known "
        "Jathakam. Once verified, this raw JSON "
        "will become a proper JathakaDeepam chart "
        "and Gemini consultation interface."
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "JathakaDeepam · ജാതകദീപം · Experimental Vedic astrology application"
)
