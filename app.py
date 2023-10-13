import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import mysql.connector as sql
import easyocr
import re
import matplotlib.pyplot as plt
import cv2
import pandas as pd
import numpy as np
import os


# storing the downloaded in cache to run it faster
@st.cache_data
def load_image():
    reader = easyocr.Reader(['en'], model_storage_directory=".")
    return reader


# making connection with mysql server
my_db = sql.connect(host='localhost',
                    user='root',
                    password='Venkat@123',
                    database='bussiness_card'
                    )
mycursor = my_db.cursor(buffered=True)

# setting the page tab
icon = Image.open('logo.jpeg')
st.set_page_config(page_title="Extracting Business Card Data with OCR",
                   page_icon=icon,
                   layout="wide",
                   initial_sidebar_state="expanded",
                   )
st.markdown("<h1 style='text-align: center; color: #051937;background-color:white;border-radius:15px;'>Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

# vertical navigation
with st.sidebar:
    selected = option_menu(None, ["Extract", "Create", "Read", "Update", "Delete"],
                           icons=["tools", "bi bi-file-text-fill", "bi bi-book",
                                  "bi bi-laptop-fill", "bi bi-cone-striped"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin-top": "20px",
                                                "--hover-color": "#266c81"},
                                   "icon": {"font-size": "20px"},
                                   "container": {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#266c81"}, })

# setting the back-ground color


def back_ground():
    st.markdown(f""" <style>.stApp {{
                        background-image: linear-gradient(to right top, #051937, #051937, #051937, #051937, #051937);;
                        background-size: cover}}
                     </style>""", unsafe_allow_html=True)


back_ground()

# conveting the image file to binary


def img_to_binary(file):
    # Convert image data to binary format
    with open(file, 'rb') as file:
        binaryData = file.read()
    return binaryData

# plotting extracted image using its dimensions


def image_preview(image, res):
    for (bbox, text, prob) in res:
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        cv2.rectangle(image, tl, br, (255, 0, 0), 2)
    plt.rcParams['figure.figsize'] = (15, 5)
    plt.axis('off')
    plt.imshow(image)

# creating a class to extract the data


class data_extract():

    # finding the phone number in the text
    def find_phone_number(text):

        try:
            pattern = reg = r"(\d{3}-\d{3}-\d{4})"
            phone_num = re.findall(pattern, text)
            if phone_num:
                pass
            else:
                pattern = reg = r"(\d{2}-\d{3}-\d{4})"
                phone_num = re.findall(pattern, text)
        except:
            phone_num = ""

        return phone_num

# regex for finding the email pattern in the text
    def finding_email(text):
        try:
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
            email = re.findall(regex, text)

        except:
            email = ""

        return email

# function to find the name
    def find_name(res1):
        try:
            name = res1[0]
        except:
            name = ""

        return name

    def filter_email_text(text):
        try:
            list = []
            email = data_extract.finding_email(text)
            for i in text.split(" "):
                if i not in email:
                    list.append(i)
        except:
            pass

        return list

# function to finding the designation
    def find_designation(res1):
        try:
            designation = res1[1]
        except:
            designation = ""

        return designation

# function to find the link
    def find_link(text):
        try:
            org = []
            text_up = data_extract.filter_email_text(text)
            for word in text_up:
                if word[-4:] == ".com":
                    org.append(word)
                    break

        except:
            org = "NA"

        if org:
            pass
        else:
            org.append("NA")

        return org

# function to finding the pincode
    def finding_pincode(text):
        try:
            regex = r"[1-9][0-9]{5}"
            pin = re.findall(regex, text)

        except:
            pin = ""

        return pin

# function to find the state
    def state(text):
        state = ""
        try:
            for word in text.split(" "):
                if word.lower()[0:5] == "tamil":
                    state = word.lower()

        except:
            pass

        if state:
            return state
        else:
            state = "NA"
            return state

# function to find the city

    def city(text):
        try:
            city = ["erode,", "salem,", "chennai,",
                    "tirupur", "hydrabad,", "karur,", "nammakal,"]
            for word in text.split(" "):
                if word.lower() in city:
                    city_f = word.lower()
                    break
                else:
                    city_f = "NA"
        except:
            city_f = ""

        return city_f

# getting company information
    def company(text):
        try:
            text = text.split(" ")
            company = text[-2:]
            company = "".join(company)
            company = [company]
        except:
            company = ""

        return company


# formatting the data in json format


def data_formatted(text, res, im):
    data = {
        'name': [],
        'designation': [],
        'contact': "",
        'email': "",
        'company': "",
        'website': "",
        'city': [],
        'state': [],
        'pincode': "",
        "image": []
    }
    data['name'].append(data_extract.find_name(res))
    data['designation'].append(data_extract.find_designation(res))
    data['contact'] = data_extract.find_phone_number(text)
    data['email'] = data_extract.finding_email(text)
    data['company'] = data_extract.company(text)
    data['website'] = data_extract.find_link(text)
    data['city'].append(data_extract.city(text))
    data['state'].append(data_extract.state(text))
    data['pincode'] = data_extract.finding_pincode(text)
    data['image'].append(im)

    return data


def convert_list_to_text(data):
    text = ""
    for i in data:
        text = text+" " + i
    return text


def convert_from_array_to_list(data):
    list = [text[1] for text in data]
    return list


def format_values(values):
    value = []
    for words in values:
        value.append(values[words][0])
    return tuple(value)


def create_table():
    mycursor.execute("""CREATE TABLE IF NOT EXISTS card_details ( 
    NAME VARCHAR(30) PRIMARY KEY,
    DESIGNATION VARCHAR(100),
    CONTACT TEXT,
    EMAIL VARCHAR(100),
    COMPANY VARCHAR(100),
    WEBSITE VARCHAR(50),
    CITY VARCHAR(50),
    STATE VARCHAR(50),
    PINCODE VARCHAR(50),
    IMAGE LONGBLOB
    )""")


create_table()

# exract page
if selected == "Extract":
    # getting the image
    img_file = st.file_uploader("Upload the Card", type=["jpeg", "png"])
    if img_file is not None:
        save_image_path = './images/' + img_file.name        # creating the path
        with open(save_image_path, "wb") as f:               # writing it as binary format
            f.write(img_file.getbuffer())
        im_binary = img_to_binary(save_image_path)
        st.image(save_image_path, use_column_width=True,     # displaying the image
                 caption="Uploaded_Image")
        with st.spinner("please wait..."):
            st.set_option('deprecation.showPyplotGlobalUse', False)
            # reading the image in cv2 to create boundaries over the text dimensions
            image = cv2.imread(save_image_path)
            render = load_image()
            # extracting the text from the image
            res = render.readtext(save_image_path)
            st.markdown("")
            st.pyplot(image_preview(image, res))             # plotting the img

        st.markdown("")
        st.markdown("")
        st.markdown("")

# uploading the extracted document into the database
        if st.button("EXTRACT TO DATABASE", type="primary",
                     disabled=False, use_container_width=True):
            box_to_array = convert_from_array_to_list(res)
            text = convert_list_to_text(box_to_array)
            data = data_formatted(text, box_to_array, im_binary)
            st.success("Uploaded to database successfully !")
            st.write(data)
            st.write(text)

            query = """INSERT INTO bussiness_card.card_details (NAME,DESIGNATION,CONTACT,EMAIL,COMPANY,WEBSITE,CITY,STATE,PINCODE,IMAGE)
        VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)"""
            value = format_values(data)
            mycursor.execute(query, value)
            my_db.commit()

# create page
if selected == "Create":

    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")

    st.markdown("#### :red[CREATE YOUR DETAILS]")
    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input(label="NAME", label_visibility="visible")
    with col2:
        designation = st.text_input(
            label="DESIGNATION", label_visibility="visible")
    with col3:
        contact = st.text_input(label="CONTACT", label_visibility="visible")

    with col1:
        email = st.text_input(label="EMAIL", label_visibility="visible")
    with col2:
        company = st.text_input(
            label="COMPANY", label_visibility="visible")
    with col3:
        website = st.text_input(label="WEBSITE", label_visibility="visible")

    with col1:
        city = st.text_input(label="CITY", label_visibility="visible")
    with col2:
        state = st.text_input(
            label="STATE", label_visibility="visible")
    with col3:
        pincode = st.text_input(label="PINCODE", label_visibility="visible")

    img1_file = st.file_uploader("Upload the Cards", type=["jpeg", "png"])

    if img1_file is not None:
        save_path = './images/'+img1_file.name
        with open(save_path, "wb") as file:
            file.write(img1_file.getbuffer())

        im_binary = img_to_binary(save_path)
        st.image(save_path,
                 caption="Uploaded_Image")

    if st.button("CREATE"):
        value = (name, designation, contact, email,
                 company, website, city, state, pincode, im_binary)

        def dict_format(values):
            data = {
                'name': [],
                'designation': [],
                'contact': [],
                'email': [],
                'company': [],
                'website': [],
                'city': [],
                'state': [],
                'pincode': [],
                'image': []
            }
            data['name'].append(values[0])
            data['designation'].append(values[1])
            data['contact'].append(values[2])
            data['email'].append(values[3])
            data['company'].append(values[4])
            data['website'].append(values[5])
            data['city'].append(values[6])
            data['state'].append(values[7])
            data['pincode'].append(values[8])
            data['image'].append(values[9])

            return data
        # inserting into the database
        dict = dict_format(value)
        st.success("uploaded to data base")
        query = """INSERT INTO bussiness_card.card_details (NAME,DESIGNATION,CONTACT,EMAIL,COMPANY,WEBSITE,CITY,STATE,PINCODE,IMAGE)
        VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)"""
        mycursor.execute(query, value)
        my_db.commit()
        st.write(dict)


if selected == "Read":

    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")

    st.markdown("#### :red[BUSSINESS CARD DETAILS]")

# reading the data from mysql
    def read_from_sql():
        query = ('SELECT NAME,DESIGNATION,CONTACT,EMAIL,COMPANY,WEBSITE,CITY,STATE,PINCODE FROM bussiness_card.card_details;')
        mycursor.execute(query)
        tabel = mycursor.fetchall()

        i = [i for i in range(1, len(tabel)+1)]
        tabel = pd.DataFrame(tabel, columns=mycursor.column_names, index=i)
        st.table(tabel)

    read_from_sql()

# update page
if selected == "Update":

    st.markdown(" ")
    st.markdown(" ")

    def name_list():
        query = "SELECT NAME FROM bussiness_card.card_details;"
        mycursor.execute(query)
        name_list = mycursor.fetchall()
        name_list = [i[0] for i in name_list]
        return name_list
    st.markdown("#### :red[SELECT THE CARD]")
    name = st.selectbox(label="Select Name", options=name_list(
    ), index=0, placeholder="Choose an option", label_visibility="visible")

    def get_selected_list(na):
        name = na
        mycursor.execute(
            "SELECT NAME,DESIGNATION,CONTACT,EMAIL,COMPANY,WEBSITE,CITY,STATE,PINCODE FROM bussiness_card.card_details where name=%s;", (name,))
        file = mycursor.fetchall()
        return file

    st.markdown(" ")
    st.markdown("#### :red[UPDATE YOUR CARD DETAILS]")
    result = get_selected_list(name)
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Name", value=result[0][0])
    with col2:
        designation = st.text_input("DESIGNATION", value=result[0][1])
    with col3:
        contact = st.text_input("CONTACT", value=result[0][2])
    with col1:
        email = st.text_input("EMAIL", value=result[0][3])
    with col2:
        company = st.text_input("COMPANY", value=result[0][4])
    with col3:
        website = st.text_input("WEBSITE", value=result[0][5])
    with col1:
        city = st.text_input("CITY", value=result[0][6])
    with col2:
        state = st.text_input("STATE", value=result[0][7])
    with col3:
        pincode = st.text_input("PINCODE", value=result[0][8])

    if st.button("Update"):
        # Update the information for the selected business card in the database
        mycursor.execute("""UPDATE card_details SET name=%s,designation=%s,contact=%s,email=%s,company=%s,website=%s,city=%s,state=%s,pincode=%s
                                    WHERE name=%s""", (name, designation, contact, email, company, website, city, state, pincode, name))
        my_db.commit()
        st.success("updated in database successfully.")


if selected == "Delete":
    st.markdown("#### :red[CARD DETAILS]")

    def read_from_sql():
        query = ('SELECT NAME,DESIGNATION,CONTACT,EMAIL,COMPANY,WEBSITE,CITY,STATE,PINCODE FROM bussiness_card.card_details;')
        mycursor.execute(query)
        tabel = mycursor.fetchall()

        i = [i for i in range(1, len(tabel)+1)]
        tabel = pd.DataFrame(tabel, columns=mycursor.column_names, index=i)
        st.table(tabel)

    read_from_sql()

    def name_list():
        query = "SELECT NAME FROM bussiness_card.card_details;"
        mycursor.execute(query)
        name_list = mycursor.fetchall()
        name_list = [i[0] for i in name_list]
        return name_list

    name = st.selectbox(label="Select Name", options=name_list(
    ), index=0, placeholder="Choose an option", label_visibility="visible")

    def delete_row(name):
        query = f"delete FROM bussiness_card.card_details where name='{name}'"
        mycursor.execute(query)
        my_db.commit()

    if st.button("DELETE FROM DATABASE"):
        delete_row(name)
        st.warning("Successfully Deleted !")
