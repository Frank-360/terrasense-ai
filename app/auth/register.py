import pandas as pd

name = st.text_input("Farmer Name")
location = st.text_input("Farm Location")
crop_type = st.text_input("Crop Type")

if st.button("Register Farmer"):
    new_data = pd.DataFrame([[name, location, crop_type]], columns=["Name","Location","Crop"])

    try:
        df = pd.read_csv("farmers.csv")
        df = pd.concat([df, new_data], ignore_index=True)
    except:
        df = new_data

    df.to_csv("farmers.csv", index=False)

    st.success("Farmer registered!")
