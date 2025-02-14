import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import json
import streamlit_survey as ss
# Login
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)
_, authentication_status, username = authenticator.login()
if authentication_status:
    st.write(f'Welcome to Phare Health!')
elif authentication_status == False:
    st.error('Username or password is incorrect!')
elif authentication_status == None:
    st.warning('Please enter your provided username and password.')
# Data directories
data_folder = "data/"
# Set reader ID
if username:
    reader_id = config['credentials']['usernames'][username]['id']
else:
    reader_id = None
if reader_id:
    @st.cache_data
    def load_data():
        with open("dummy_data.json", "r") as f:
            return json.load(f)
    data = load_data()
    # Select document to annotate
    doc_indices = [d['id'] for d in data]
    if "doc_select" not in st.session_state:
        st.session_state["doc_select"] = doc_indices[0]
    doc_idx = st.selectbox("Select document index", options=doc_indices, index=doc_indices.index(st.session_state["doc_select"]))
    document = next(d for d in data if d['id'] == doc_idx)
    st.subheader(document['specialty'])
    # Highlighting function
    colors = ["#FFDDC1", "#C1E1FF", "#C1FFC1", "#FFC1E1"]
    def highlight_text(doc, codes):
        for i, code_dict in enumerate(codes):
            for code, span in code_dict.items():
                doc = doc.replace(span, f'<span style="background-color:{colors[i % len(colors)]};">{span}</span>')
        return doc
    st.markdown(highlight_text(document['document'], document['codes']), unsafe_allow_html=True)
    results = []
    survey = ss.StreamlitSurvey()
    page_length = min(4, len(document['codes']))
    pages = survey.pages(page_length, progress_bar=True, on_submit=lambda: st.success("Submitted!"))
    with pages:
        def next_sample():
            current_idx = doc_indices.index(st.session_state["doc_select"])
            if current_idx < len(doc_indices) - 1:
                st.session_state["doc_select"] = doc_indices[current_idx + 1]
                pages.current = 0
            else:
                st.success("No more documents left!")
                st.stop()
        pages.submit_button = lambda pages: st.button(
            "Next Document",
            type="primary",
            use_container_width=True,
            on_click=next_sample,
        )
        item = document['codes'][pages.current]
        code = list(item.keys())[0]
        span = list(item.values())[0]
        st.markdown(f'**Code: {code}**')
        span_with_highlight = f'<span style="background-color:{colors[pages.current % len(colors)]};">{span}</span>'
        st.markdown(f"**Extracted Span:** {span_with_highlight}", unsafe_allow_html=True)
        response = st.radio("Is this code correct?", ["Yes", "No", "Should not be coded"], key=f"{doc_idx}_{code}_response_{pages.current}")
        notes = st.text_area("Notes (Feedback, Explanation, or Missing Codes)", key=f"{doc_idx}_{code}_notes_{pages.current}")
        results.append({"code": code, "response": response, "notes": notes})
