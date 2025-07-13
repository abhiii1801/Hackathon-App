import streamlit as st
import json
import pandas as pd
import time

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

def register_student(username, password, name, email):
    students = load_json('students.json')
    if any(s['username'] == username for s in students):
        return False
    students.append({"username": username, "password": password, "name": name, "email": email})
    save_json('students.json', students)
    return True

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
    st.set_page_config(page_title="InsightX Innovators Quiz", page_icon="🧑‍💻", layout="centered", initial_sidebar_state="auto")
    st.title("🧑‍💻 InsightX Innovators Quiz App")
    # Hide sidebar and menu after login
    if st.session_state.get('user'):
        st.markdown("""
            <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"] {display: none !important;}
            </style>
        """, unsafe_allow_html=True)
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if not st.session_state.get('user'):
        if 'choice' not in st.session_state:
            st.session_state.choice = "Login"
        menu = ["Login", "Register"]
        st.sidebar.title("Menu")
        st.session_state.choice = st.sidebar.selectbox("Menu", menu, index=menu.index(st.session_state.choice))
        choice = st.session_state.choice
        if choice == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if get_admin(username, password):
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
        elif choice == "Register":
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Register"):
                if register_student(username, password, name, email):
                    st.success("Registration successful. Please login.")
                else:
                    st.error("Username already exists.")
    # Main app after login
    if st.session_state.user:
        st.markdown("""
            <style>
            [data-testid='stSidebar'], [data-testid='stSidebarNav'] {display: none !important;}
            </style>
        """, unsafe_allow_html=True)
        if st.session_state.is_admin:
            st.header("Admin Dashboard")
            st.subheader("Leaderboard")
            leaderboard = get_leaderboard()
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
            student = get_student(st.session_state.user)
            st.header(f"Welcome, {student['name']}")
            st.write(f"Email: {student['email']}")
            st.download_button("Download Dataset", data=open('sample_dataset.csv', 'rb').read(), file_name="dataset.csv")
            st.subheader("Quiz")
            questions = load_json('questions.json')
            answers = {}
            for q in questions:
                st.markdown(f"**Q{q['id']}: {q['question']}**")
                if q['type'] == 'numeric':
                    ans = st.number_input(f"Your answer (Q{q['id']})", key=f"q{q['id']}")
                elif q['type'] == 'msq':
                    ans = st.multiselect(f"Select all that apply (Q{q['id']})", q['options'], key=f"q{q['id']}")
                elif q['type'] == 'mcq':
                    ans = st.radio(f"Select one (Q{q['id']})", q['options'], key=f"q{q['id']}")
                else:
                    ans = None
                answers[str(q['id'])] = ans
            if st.button("Submit Quiz"):
                # Evaluate
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
                submissions = load_json('submissions.json')
                found = False
                for sub in submissions:
                    if sub['username'] == student['username']:
                        sub['answers'] = answers
                        sub['marks'] = total
                        found = True
                        break
                if not found:
                    submissions.append({"username": student['username'], "answers": answers, "marks": total})
                save_json('submissions.json', submissions)
                st.success("Quiz submitted! Your marks will be updated on the leaderboard shortly.")
                time.sleep(2)
                st.session_state.user = None
                st.session_state.is_admin = False
                st.session_state.choice = "Login"
                st.rerun()

if __name__ == "__main__":
    main()
