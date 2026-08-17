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
        max-width: 820px;
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
        max-width: 540px;
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

    .jd-panel {
        border: 1px solid rgba(198,166,106,0.14);
        background: rgba(255,255,255,0.022);
        border-radius: 18px;
        padding: 1.15rem 1.25rem;
        margin: 0.65rem 0 1rem 0;
    }

    .jd-panel-gold {
        border: 1px solid rgba(198,166,106,0.22);
        background: rgba(198,166,106,0.055);
        border-radius: 18px;
        padding: 1.15rem 1.25rem;
        margin: 0.65rem 0 1rem 0;
    }

    .jd-kicker {
        color: #a99065;
        text-transform: uppercase;
        letter-spacing: .14em;
        font-size: .68rem;
        margin-bottom: .25rem;
    }

    .jd-value {
        color: #f0e5d0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.28rem;
        margin-bottom: .25rem;
    }

    .jd-muted {
        color: #8c867d;
        font-size: .86rem;
        line-height: 1.5;
    }

    .jd-section-label {
        color: #b69b69;
        text-transform: uppercase;
        letter-spacing: .16em;
        font-size: .69rem;
        margin-top: 1.2rem;
        margin-bottom: .3rem;
    }

    .jd-approved {
        padding: 1.2rem 1.3rem;
        border-radius: 18px;
        border: 1px solid rgba(114, 187, 132, .28);
        background: rgba(114, 187, 132, .065);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .jd-approved-title {
        font-size: 1.05rem;
        color: #bfe1c6;
        font-weight: 600;
        margin-bottom: .2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

VEDIC_PLANET_NAMES = {
    "Sun": "Surya / Ravi",
    "Moon": "Chandra",
    "Mercury": "Budha",
    "Venus": "Shukra",
    "Mars": "Kuja / Mangala",
    "Jupiter": "Guru / Brihaspati",
    "Saturn": "Shani",
    "Rahu": "Rahu",
    "Ketu": "Ketu",
    "Ascendant": "Lagna",
}


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

    return ApiClient(client_id, client_secret)


@st.cache_data(ttl=86400)
def resolve_birthplace(place):
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

    timezone_name = get_timezone_finder().timezone_at(
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


def create_birth_datetime(birth_date, birth_time, timezone_name):
    timezone = ZoneInfo(timezone_name)
    birth_datetime = datetime.combine(birth_date, birth_time)
    birth_datetime = birth_datetime.replace(tzinfo=timezone)
    return birth_datetime.isoformat()


def get_astrology_data(birth_datetime, latitude, longitude):
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


def degree_to_dms(value):
    """
    Format decimal degrees inside a sign as degrees/minutes/seconds.
    Example: 27.7727 -> 27° 46′ 22″
    """
    value = float(value or 0)
    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)

    if seconds == 60:
        seconds = 0
        minutes += 1

    if minutes == 60:
        minutes = 0
        degrees += 1

    return f"{degrees}° {minutes:02d}′ {seconds:02d}″"


def get_kundli_parts(astrology_data):
    kundli = (
        astrology_data
        .get("kundli", {})
        .get("data", {})
    )

    nak = kundli.get("nakshatra_details", {})
    mangal = kundli.get("mangal_dosha", {})
    yoga = kundli.get("yoga_details", [])

    return kundli, nak, mangal, yoga


def get_planets(astrology_data):
    return (
        astrology_data
        .get("planet_positions", {})
        .get("data", {})
        .get("planet_position", [])
    )


def find_planet(planets, name):
    return next(
        (p for p in planets if p.get("name") == name),
        None
    )


def rasi_label(rasi_obj):
    if not rasi_obj:
        return "—"
    name = rasi_obj.get("name", "—")
    lord = rasi_obj.get("lord", {})
    lord_name = lord.get("vedic_name") or lord.get("name")
    if lord_name:
        return f"{name} · Lord: {lord_name}"
    return name


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "astrology_data" not in st.session_state:
    st.session_state.astrology_data = None

if "birth_profile" not in st.session_state:
    st.session_state.birth_profile = None

if "calculation_verified" not in st.session_state:
    st.session_state.calculation_verified = False

if "result_stage" not in st.session_state:
    st.session_state.result_stage = "results"


def reset_chart():
    st.session_state.astrology_data = None
    st.session_state.birth_profile = None
    st.session_state.calculation_verified = False
    st.session_state.result_stage = "results"


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="jd-symbol">✦</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="jd-eyebrow">Vedic Astrology · AI Consultation</div>',
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
        Enter your birth details to create your Vedic horoscope.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------

if st.session_state.astrology_data is None:

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
            "Calculation method: Vedic Sidereal · Lahiri Ayanamsa"
        )

        generate = st.form_submit_button(
            "Generate Jathakam →",
            use_container_width=True,
        )

    if generate:

        if not birthplace.strip():
            st.error("Please enter your place of birth.")
            st.stop()

        try:
            with st.status(
                "Preparing your Jathakam…",
                expanded=True
            ) as status:

                st.write("Finding birthplace coordinates…")

                location = resolve_birthplace(
                    birthplace.strip()
                )

                st.write(
                    f"Found **{location['name']}**"
                )

                st.write("Determining local timezone…")

                iso_datetime = create_birth_datetime(
                    birth_date,
                    birth_time,
                    location["timezone"],
                )

                st.write(
                    f"Timezone: **{location['timezone']}**"
                )

                st.write("Calculating Vedic horoscope…")

                astrology_data = get_astrology_data(
                    iso_datetime,
                    location["latitude"],
                    location["longitude"],
                )

                st.session_state.astrology_data = astrology_data
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
                st.session_state.calculation_verified = False
                st.session_state.result_stage = "results"

                status.update(
                    label="Jathakam calculated",
                    state="complete",
                    expanded=False,
                )

            st.rerun()

        except Exception as error:
            st.error(
                "JathakaDeepam couldn't generate the horoscope."
            )
            st.exception(error)


# ---------------------------------------------------------
# FORMATTED RESULTS
# ---------------------------------------------------------

if st.session_state.astrology_data is not None:

    data = st.session_state.astrology_data
    profile = st.session_state.birth_profile

    kundli, nak, mangal, yoga_details = get_kundli_parts(data)
    planets = get_planets(data)

    nakshatra = nak.get("nakshatra", {})
    chandra_rasi = nak.get("chandra_rasi", {})
    soorya_rasi = nak.get("soorya_rasi", {})
    western_zodiac = nak.get("zodiac", {})
    additional = nak.get("additional_info", {})

    ascendant = find_planet(planets, "Ascendant")

    st.divider()

    # -----------------------------------------------------
    # APPROVED / NEXT-STAGE SCREEN
    # -----------------------------------------------------

    if st.session_state.calculation_verified:
        st.markdown("## Jathakam Verified")

        st.markdown(
            f"""
            <div class="jd-approved">
                <div class="jd-approved-title">
                    ✓ Calculation approved
                </div>
                <div class="jd-muted">
                    The birth chart for <b>{profile.get("name") or "this profile"}</b>
                    has been accepted as the horoscope source for the next stage.
                    JathakaDeepam can now use this verified chart for interpretation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "← Review Horoscope",
                use_container_width=True,
            ):
                st.session_state.calculation_verified = False
                st.rerun()

        with c2:
            if st.button(
                "Create Another Jathakam",
                use_container_width=True,
            ):
                reset_chart()
                st.rerun()

        st.markdown("### Next stage")

        st.markdown(
            """
            <div class="jd-panel-gold">
                <div class="jd-kicker">Ready for AI Consultation</div>
                <div class="jd-value">Your verified chart is saved in this session.</div>
                <div class="jd-muted">
                    The next build will connect this verified horoscope to the
                    Gemini astrologer chat. Gemini will interpret these calculated
                    values rather than inventing planetary positions itself.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.stop()

    # -----------------------------------------------------
    # RESULTS HEADER
    # -----------------------------------------------------

    st.markdown("## Your Jathakam")

    if profile.get("name"):
        st.markdown(
            f"""
            <div class="jd-panel-gold">
                <div class="jd-kicker">Birth Profile</div>
                <div class="jd-value">{profile["name"]}</div>
                <div class="jd-muted">
                    {profile["date"]} · {profile["time"]}<br>
                    {profile["place"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # KEY HOROSCOPE SUMMARY
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Core Horoscope</div>',
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns(2)

    lagna_name = (
        ascendant.get("rasi", {}).get("name", "—")
        if ascendant else "—"
    )
    lagna_degree = (
        degree_to_dms(ascendant.get("degree"))
        if ascendant else ""
    )

    with m1:
        st.metric(
            "Lagna / Ascendant",
            lagna_name,
            lagna_degree,
        )

    with m2:
        st.metric(
            "Nakshatra",
            nakshatra.get("name", "—"),
            f'Pada {nakshatra.get("pada", "—")}',
        )

    m3, m4 = st.columns(2)

    with m3:
        st.metric(
            "Chandra Rasi / Moon Sign",
            chandra_rasi.get("name", "—"),
            (
                chandra_rasi
                .get("lord", {})
                .get("vedic_name", "")
            ),
        )

    with m4:
        st.metric(
            "Soorya Rasi / Sun Sign",
            soorya_rasi.get("name", "—"),
            (
                soorya_rasi
                .get("lord", {})
                .get("vedic_name", "")
            ),
        )

    if western_zodiac.get("name"):
        st.caption(
            f'Western zodiac: {western_zodiac["name"]} · '
            f'Ayanamsa: {profile["ayanamsa"]} · '
            f'Chart preference: {profile["chart_style"]}'
        )

    # -----------------------------------------------------
    # BIRTH PROFILE
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Birth Details</div>',
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)

    with b1:
        st.markdown(
            f"""
            <div class="jd-panel">
                <div class="jd-kicker">Birth</div>
                <div class="jd-value">{profile["date"]}</div>
                <div class="jd-muted">
                    Time: {profile["time"]}<br>
                    Timezone: {profile["timezone"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b2:
        st.markdown(
            f"""
            <div class="jd-panel">
                <div class="jd-kicker">Calculation</div>
                <div class="jd-value">{profile["ayanamsa"]}</div>
                <div class="jd-muted">
                    Sidereal Vedic Astrology<br>
                    Consultation: {profile["language"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Location & technical birth details"):
        st.write(f"**Resolved place:** {profile['place']}")
        st.write(
            f"**Coordinates:** "
            f"{profile['latitude']:.6f}, {profile['longitude']:.6f}"
        )
        st.write(f"**Timezone:** {profile['timezone']}")
        st.write(f"**Birth datetime:** {profile['datetime']}")

    # -----------------------------------------------------
    # NAKSHATRA
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Nakshatra</div>',
        unsafe_allow_html=True,
    )

    nak_lord = nakshatra.get("lord", {})

    st.markdown(
        f"""
        <div class="jd-panel-gold">
            <div class="jd-kicker">Janma Nakshatra</div>
            <div class="jd-value">
                {nakshatra.get("name", "—")} · Pada {nakshatra.get("pada", "—")}
            </div>
            <div class="jd-muted">
                Lord: {nak_lord.get("name", "—")}
                ({nak_lord.get("vedic_name", "—")}) ·
                Deity: {additional.get("deity", "—")} ·
                Gana: {additional.get("ganam", "—")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Traditional Nakshatra attributes"):
        attr_rows = [
            {"Attribute": "Symbol", "Value": additional.get("symbol", "—")},
            {"Attribute": "Animal sign", "Value": additional.get("animal_sign", "—")},
            {"Attribute": "Nadi", "Value": additional.get("nadi", "—")},
            {"Attribute": "Colour", "Value": additional.get("color", "—")},
            {"Attribute": "Best direction", "Value": additional.get("best_direction", "—")},
            {"Attribute": "Syllables", "Value": additional.get("syllables", "—")},
            {"Attribute": "Birth stone", "Value": additional.get("birth_stone", "—")},
            {"Attribute": "Traditional gender", "Value": additional.get("gender", "—")},
            {"Attribute": "Planet", "Value": additional.get("planet", "—")},
            {"Attribute": "Enemy yoni", "Value": additional.get("enemy_yoni", "—")},
        ]
        st.dataframe(
            attr_rows,
            hide_index=True,
            use_container_width=True,
        )

    # -----------------------------------------------------
    # MANGAL DOSHA
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Mangal Dosha</div>',
        unsafe_allow_html=True,
    )

    has_dosha = bool(mangal.get("has_dosha", False))

    if has_dosha:
        st.warning(
            f'**Manglik / Mangal Dosha detected**\n\n'
            f'{mangal.get("description", "")}'
        )
    else:
        st.success(
            f'**No Mangal Dosha detected**\n\n'
            f'{mangal.get("description", "")}'
        )

    # -----------------------------------------------------
    # YOGAS
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Yoga Overview</div>',
        unsafe_allow_html=True,
    )

    if yoga_details:
        yoga_rows = []
        for item in yoga_details:
            yoga_rows.append({
                "Category": item.get("name", "—"),
                "Summary": item.get("description", "—"),
            })

        st.dataframe(
            yoga_rows,
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("No yoga summary returned by the API.")

    # -----------------------------------------------------
    # PLANET POSITIONS
    # -----------------------------------------------------

    st.markdown(
        '<div class="jd-section-label">Planetary Positions</div>',
        unsafe_allow_html=True,
    )

    planet_rows = []

    for planet in planets:
        planet_name = planet.get("name", "—")
        rasi = planet.get("rasi", {})
        ruler = rasi.get("lord", {})

        planet_rows.append({
            "Planet": planet_name,
            "Vedic name": VEDIC_PLANET_NAMES.get(planet_name, "—"),
            "Rasi": rasi.get("name", "—"),
            "Degree": degree_to_dms(planet.get("degree", 0)),
            "Rasi lord": ruler.get("vedic_name") or ruler.get("name", "—"),
            "Retrograde": (
                "Yes"
                if planet.get("is_retrograde")
                else "No"
            ),
        })

    st.dataframe(
        planet_rows,
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Degrees shown above are the planet's position within its Rasi."
    )

    # -----------------------------------------------------
    # DEBUG JSON
    # -----------------------------------------------------

    with st.expander("Developer data · Raw Prokerala response"):
        st.caption(
            "Hidden from normal reading flow. Useful only while developing "
            "or troubleshooting JathakaDeepam."
        )

        t1, t2, t3 = st.tabs(
            ["Birth Profile JSON", "Kundli JSON", "Planet JSON"]
        )

        with t1:
            st.json(profile)

        with t2:
            st.json(data["kundli"])

        with t3:
            st.json(data["planet_positions"])

    # -----------------------------------------------------
    # APPROVAL FLOW
    # -----------------------------------------------------

    st.divider()

    st.markdown("### Verify this Jathakam")

    st.write(
        "Please compare the **Lagna, Nakshatra, Chandra Rasi and "
        "planetary positions** with a horoscope you trust before "
        "using the AI interpretation."
    )

    action1, action2 = st.columns(2)

    with action1:
        if st.button(
            "✓ Approve & Continue →",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.calculation_verified = True
            st.rerun()

    with action2:
        if st.button(
            "↻ Change Birth Details",
            use_container_width=True,
        ):
            reset_chart()
            st.rerun()


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "JathakaDeepam · ജാതകദീപം · Experimental Vedic astrology application"
)
