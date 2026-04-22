import streamlit as st

st.subheader("Farmer Registration")

name = st.text_input("Farmer Name")
location = st.text_input("Farm Location")
crop = st.text_input("Crop Type")

if st.button("Submit"):
    st.success("Registration received")