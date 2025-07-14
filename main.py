import streamlit as st
st.set_page_config(page_title="InsightX Innovators Quiz Part 2", page_icon="🧑‍💻", layout="centered", initial_sidebar_state="auto")

import json
import pandas as pd
import time

st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK, ._terminalButton_rix23_138 {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            button[data-testid="manage-app-button"] {
                display: none !important;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_student(username):
    students = load_json('students.json')
    for s in students:
        if s['username'] == username:
            return s
    return None

def get_admin(username, password):
    return username == 'admin' and password == 'admin123'

def register_student(username, password, name):
    students = load_json('students.json')
    if any(s['username'] == username for s in students):
        return False
    students.append({"username": username, "password": password, "name": name})
    save_json('students.json', students)
    return True

def load_active_quiz():
    quizzes = load_json('quizzes.json')
    if 'active_quiz' not in st.session_state:
        st.session_state.active_quiz = quizzes[0]['quiz_id']
    return quizzes, st.session_state.active_quiz

def set_active_quiz(quiz_id):
    st.session_state.active_quiz = quiz_id

def get_quiz_questions(quiz_id):
    quizzes = load_json('quizzes.json')
    for quiz in quizzes:
        if quiz['quiz_id'] == quiz_id:
            return load_json(quiz['questions_file'])
    return []

def load_submissions():
    try:
        return load_json('submissions.json')
    except:
        return {}

def save_submissions(subs):
    save_json('submissions.json', subs)

def get_leaderboard():
    submissions = load_json('submissions.json')
    students = {s['username']: s for s in load_json('students.json')}
    leaderboard = []
    for sub in submissions:
        info = students.get(sub['username'], {})
        leaderboard.append({
            'username': sub['username'],
            'name': info.get('name', ''),
            'marks': sub['marks'],
            'answers': sub['answers']
        })
    leaderboard.sort(key=lambda x: x['marks'], reverse=True)
    return leaderboard

def main():
    st.title("🧑‍💻 InsightX Innovators Quiz App")
    # Hide sidebar and menu after login
    if st.session_state.get('user'):
        st.markdown("""
            <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"] {display: none !important;}
            </style>
        """, unsafe_allow_html=True)
    # Remove sidebar/navbar and use buttons for login/register
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'choice' not in st.session_state:
        st.session_state.choice = "Login"
    if not st.session_state.get('user'):
        st.markdown("""
            <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"] {display: none !important;}
            </style>
        """, unsafe_allow_html=True)
        if st.session_state.choice == "Login":
            st.markdown("### Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_col, register_col = st.columns([1, 1])
            with login_col:
                login_clicked = st.button("Login")
            with register_col:
                register_clicked = st.button("Register")
            if register_clicked:
                st.session_state.choice = "Register"
                st.rerun()
            if login_clicked:
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif get_admin(username, password):
                    st.session_state.user = 'admin'
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    student = get_student(username)
                    if student and student['password'] == password:
                        st.session_state.user = username
                        st.session_state.is_admin = False
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        elif st.session_state.choice == "Register":
            st.markdown("### Register")
            name = st.text_input("Full Name", key="register_name")
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            reg_col, login_col = st.columns([1, 1])
            with reg_col:
                submit_reg = st.button("Submit Registration")
            with login_col:
                login_btn = st.button("Login", key="register_login_btn")
            if submit_reg:
                if not name or not username or not password:
                    st.error("Please fill in all fields.")
                elif register_student(username, password, name):
                    st.success("Registration successful. Please login.")
                    st.session_state.choice = "Login"
                else:
                    st.error("Username already exists.")
            if login_btn:
                st.session_state.choice = "Login"
                st.rerun()
    # Main app after login
    if st.session_state.user:
        st.markdown("""
            <style>
            [data-testid='stSidebar'], [data-testid='stSidebarNav'] {display: none !important;}
            </style>
        """, unsafe_allow_html=True)
        quizzes, active_quiz = load_active_quiz()
        if st.session_state.is_admin:
            st.header("Admin Dashboard")
            st.subheader("Select Active Quiz")
            quiz_names = {q['quiz_id']: q['name'] for q in quizzes}
            selected_quiz = st.selectbox("Active Quiz", options=list(quiz_names.keys()), format_func=lambda x: quiz_names[x], index=[q['quiz_id'] for q in quizzes].index(active_quiz))
            if selected_quiz != active_quiz:
                set_active_quiz(selected_quiz)
                st.rerun()
            st.subheader("Leaderboard")
            submissions = load_submissions()
            leaderboard = []
            students = {s['username']: s for s in load_json('students.json')}
            for sub in submissions.get(active_quiz, []):
                info = students.get(sub['username'], {})
                leaderboard.append({
                    'username': sub['username'],
                    'name': info.get('name', ''),
                    'marks': sub['marks'],
                    'answers': sub['answers']
                })
            leaderboard.sort(key=lambda x: x['marks'], reverse=True)
            if leaderboard:
                df = pd.DataFrame(leaderboard)[['username', 'name', 'marks']]
                df.index += 1
                st.markdown(
                    df.style
                    .background_gradient(cmap="Blues", subset=["marks"])
                    .format({"marks": "{:d}"})
                    .set_table_styles([
                        {"selector": "th", "props": [("background-color", "#f0f2f6"), ("color", "#222")]},
                        {"selector": "td", "props": [("background-color", "#fff"), ("color", "#222")]}])
                    .hide(axis='index')
                    .to_html(),
                    unsafe_allow_html=True
                )
            else:
                st.info("No submissions yet.")
            st.subheader("All Submissions")
            for entry in leaderboard:
                st.markdown(f"**{entry['name']} ({entry['username']})**: {entry['marks']} points")
                ans_table = []
                for qid, ans in entry['answers'].items():
                    if isinstance(ans, list):
                        ans_str = ', '.join(str(a) for a in ans)
                    else:
                        ans_str = str(ans)
                    ans_table.append({"Question ID": qid, "Answer": ans_str})
                st.table(pd.DataFrame(ans_table))
        else:
            quizzes, active_quiz = load_active_quiz()
            quiz_names = {q['quiz_id']: q['name'] for q in quizzes}
            st.header(f"Welcome, {get_student(st.session_state.user)['name']}")
            st.subheader(f" {quiz_names[active_quiz]}")
            # Add back the dataset download button if the quiz has dataset questions
            questions = get_quiz_questions(active_quiz)
            if any(q.get('dataset_required', False) for q in questions):
                st.write(f"Download this file to continue: ") 
                st.download_button("Download Dataset", data=open('sample_dataset.csv', 'rb').read(), file_name="dataset.csv")
            submissions = load_submissions()
            # Fix: handle both dict and legacy list format for submissions.json
            if isinstance(submissions, dict):
                quiz_subs = submissions.get(active_quiz, [])
            else:
                quiz_subs = submissions  # fallback for legacy list format
            already_submitted = any(sub['username'] == st.session_state.user for sub in quiz_subs)
            if already_submitted:
                st.info("You have already submitted this quiz. You cannot attempt it again.")
            else:
                questions = get_quiz_questions(active_quiz)
                answers = {}
                for q in questions:
                    st.markdown(f"**Q{q['id']}: {q['question']}**")
                    if q['type'] == 'numeric':
                        ans = st.number_input(f"Your answer (Q{q['id']})", key=f"q{active_quiz}_{q['id']}")
                    elif q['type'] == 'msq':
                        ans = st.multiselect(f"Select all that apply (Q{q['id']})", q['options'], key=f"q{active_quiz}_{q['id']}")
                    elif q['type'] == 'mcq':
                        ans = st.radio(f"Select one (Q{q['id']})", q['options'], key=f"q{active_quiz}_{q['id']}")
                    else:
                        ans = None
                    answers[str(q['id'])] = ans
                if st.button("Submit Quiz"):
                    total = 0
                    for q in questions:
                        user_ans = answers[str(q['id'])]
                        correct = q['correct_answer']
                        if q['type'] == 'numeric':
                            if abs(user_ans - correct) < 1e-3:
                                total += q['points']
                        elif q['type'] == 'msq':
                            if set(user_ans) == set(correct):
                                total += q['points']
                        elif q['type'] == 'mcq':
                            if user_ans == correct:
                                total += q['points']
                    # Save submission
                    if isinstance(submissions, dict):
                        if active_quiz not in submissions:
                            submissions[active_quiz] = []
                        submissions[active_quiz].append({"username": st.session_state.user, "answers": answers, "marks": total})
                    else:
                        submissions.append({"username": st.session_state.user, "answers": answers, "marks": total})
                    save_submissions(submissions)
                    st.success("Quiz submitted! Your marks will be updated on the leaderboard shortly.")
                    time.sleep(2)
                    st.session_state.user = None
                    st.session_state.is_admin = False
                    st.session_state.choice = "Login"
                    st.rerun()

if __name__ == "__main__":
    main()
