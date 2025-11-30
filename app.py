import streamlit as st
import pandas as pd
import requests
import pickle
import gdown
import os
# PAGE CONFIG

st.set_page_config(page_title="Movie Recommender", layout="wide")

# Tiny theme switch UI
# Initialize theme in session_state
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Toggle button
if st.button(label="theme",key="theme_toggle"):
    # Toggle the theme value
    if st.session_state.theme == "light":
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"
# THEME COLORS

if st.session_state.theme == "light":
    bg_color = "#FFFFFF"
    text_color = "#000000"
    input_bg = "#F0F0F0"
    input_text = "#000000"
else:
    bg_color = "#0E1117"
    text_color = "#FFFFFF"
    input_bg = "#262730"
    input_text = "#FFFFFF"


# Apply theme CSS
st.markdown(
    f"""
    <style>
        body, .stApp ,stbutton{{
            background-color: {bg_color};
            color: {text_color};
        }}
        .movie-title {{
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            margin-top: 10px;
            color: {text_color};
        }}
        .overview-box {{
            padding: 10px;
            background-color: #2a2a2a22;
            border-radius: 8px;
            font-size: 14px;
        }}
        input[type="text"] {{
    background-color: {input_bg} !important;
    color: {input_text} !important;
}}
    label{{
    color: {text_color} !important;
    }}
   div.stButton > button{{
    background-color: transparent !important;  /* Button background */
    color: {text_color} !important;          /* Text color */
    border: none !important;
}}

/* Hover effect */
div.stButton > button:hover {{
    background-color: {input_text} !important;  
    color:white !important;  /* Hover color */
}}


    </style>
    """,
    unsafe_allow_html=True
)
def download_pickle():
    # Movie dictionary
    if not os.path.exists("movie_dict.pkl"):
        url = "https://drive.google.com/uc?id=YOUR_MOVIE_DICT_FILE_ID"
        gdown.download(url, "movie_dict.pkl", quiet=False, fuzzy=True)

# LOAD DATA

@st.cache_resource
@st.cache_data.clear()  # Clears cached pickle if corrupted

def load_data():
    download_pickle()
    with open("movie_dict.pkl", "rb") as f:
        movie, cosine_sim = pickle.load(f)
    return movie, cosine_sim

movie, cosine_sim = load_data()

# GET RECOMMENDATIONS

@st.cache_data
def get_recommendations(title):
    idx = movie[movie['title'] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_scores = sim_scores[1:11]  # top 10

    movie_indices = [i[0] for i in top_scores]
    return movie.iloc[movie_indices][['title', 'movie_id']].reset_index(drop=True)


# TMDB DETAILS

API_KEY = "a4993591774d49b5a7d1ab7e258e890b"

@st.cache_data
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    data = requests.get(url).json()

    poster_path = data.get("poster_path")
    overview = data.get("overview", "No overview available.")
    rating = data.get("vote_average", "N/A")
    popularity = data.get("popularity", "N/A")

    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
    else:
        poster_url = "https://via.placeholder.com/500x750?text=No+Image"

    return poster_url, overview, rating, popularity


# SEARCH BAR + AUTOCOMPLETE

st.title("🎬 Movie Recommender System")

search_text = st.text_input(label="🔍 Search for a movie")

if search_text:
    matches = movie[movie["title"].str.contains(search_text, case=False, na=False)]["title"].head(10)
    if len(matches) == 0:
        st.warning("No matches found.")
        selected_movie = None
    else:
        selected_movie = st.selectbox("Select a movie:", matches)
else:
    selected_movie = st.selectbox("Or choose from all movies:", movie["title"].values)


# DISPLAY SELECTED MOVIE INFO

if selected_movie:
    movie_id = movie[movie["title"] == selected_movie]["movie_id"].iloc[0]
    poster, overview, rating, popularity = fetch_movie_details(movie_id)

    colA, colB = st.columns([1, 2])

    with colA:
        st.image(poster, width=150)

    with colB:
        st.subheader(selected_movie)
        st.markdown(f"⭐ **Rating:** {rating}")
        st.markdown(f"🔥 **Popularity:** {popularity}")
        st.markdown(f"<div class='overview-box'>{overview}</div>", unsafe_allow_html=True)


# SHOW RECOMMENDATIONS
#clicked movie details
recs = get_recommendations(selected_movie)  # your existing function

st.write(f"### 🔥 Top 10 Movies Similar to **{selected_movie}**")
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
for i in range(0, 10, 5):
    cols = st.columns(5)
    for col, j in zip(cols, range(i, i + 5)):
        if j < len(recs):
            movie_title = recs.iloc[j]["title"]
            movie_id = recs.iloc[j]["movie_id"]
            poster_url, _, rating, popularity = fetch_movie_details(movie_id)

            with col:
                # Show poster
                st.image(poster_url, width=150)
                
                # Use a button for movie title
                if st.button(movie_title, key=f"rec_btn_{j}"):
                    st.session_state.selected_movie = movie_title

# If a movie has been clicked in recommendations
if st.session_state.selected_movie:
    movie_id = movie[movie['title'] == st.session_state.selected_movie]["movie_id"].iloc[0]
    poster, overview, rating, popularity = fetch_movie_details(movie_id)

    colA, colB = st.columns([1, 2])
    with colA:
        st.image(poster, width=150)
    with colB:
        st.subheader(st.session_state.selected_movie)
        st.markdown(f"⭐ **Rating:** {rating}")
        st.markdown(f"🔥 **Popularity:** {popularity}")
        st.markdown(f"<div class='overview-box'>{overview}</div>", unsafe_allow_html=True)
