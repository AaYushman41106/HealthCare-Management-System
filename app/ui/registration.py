"""Streamlit Patient Registration — Guided Onboarding Experience."""
from datetime import date
import streamlit as st
from app.db.database import SessionLocal
from app.services.auth_service import AuthService


def render_registration_page() -> None:
    """Render an elegant patient self-registration interface."""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("# SecureCare")
        st.markdown("### Patient Account Registration")
        st.caption("Enroll securely to schedule consultations, communicate with clinical specialists, and access your health records.")
        st.divider()

        with st.container(border=True):
            st.markdown("#### Account & Demographic Profile")
            st.caption("All submitted records are protected by strict healthcare access boundaries.")

            with st.form("patient_registration_form"):
                col_u, col_e = st.columns(2)
                with col_u:
                    username = st.text_input("Preferred Username *", placeholder="e.g. alice_w")
                with col_e:
                    email = st.text_input("Personal Email Address *", placeholder="e.g. alice@example.com")

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    password = st.text_input("Confidential Password *", type="password", placeholder="Min. 8 characters")
                with col_p2:
                    confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Repeat password")

                st.divider()
                st.markdown("##### Clinical & Demographic Details")

                full_name = st.text_input("Full Legal Name *", placeholder="e.g. Alice Wonder")

                col_dob, col_gen = st.columns(2)
                with col_dob:
                    dob = st.date_input(
                        "Date of Birth *",
                        value=date(1995, 6, 15),
                        min_value=date(1900, 1, 1),
                        max_value=date.today(),
                    )
                with col_gen:
                    gender = st.selectbox("Gender *", options=["Female", "Male", "Other", "Prefer not to say"])

                phone = st.text_input("Primary Contact Phone", placeholder="+1 (555) 019-2834")
                address = st.text_area("Residential Address", placeholder="Street, City, Postal Code")

                submit_btn = st.form_submit_button(
                    "Create Patient Account",
                    type="primary",
                    use_container_width=True,
                )

            if submit_btn:
                if not username or not email or not password or not full_name:
                    st.warning("Please complete all required fields marked with an asterisk (*).")
                elif len(password) < 8:
                    st.warning("Password must be at least 8 characters long.")
                elif password != confirm_password:
                    st.error("Passwords do not match. Please verify your password entry.")
                else:
                    db = SessionLocal()
                    try:
                        patient, err = AuthService.register_patient(
                            db=db,
                            username=username.strip(),
                            email=email.strip().lower(),
                            password=password,
                            full_name=full_name.strip(),
                            date_of_birth=dob,
                            gender=gender,
                            phone=phone.strip() if phone else None,
                            address=address.strip() if address else None,
                        )
                        if patient:
                            st.success(f"Account for {full_name} created successfully. You may now sign in.")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(err or "Unable to complete registration. Username or email may already be in use.")
                    finally:
                        db.close()

            st.divider()
            if st.button("← Return to Sign In", use_container_width=True, type="secondary"):
                st.session_state.show_register = False
                st.rerun()

        with st.container(border=True):
            st.caption("🔒 **Security & Privacy Commitment**")
            st.caption(
                "Your health records are confidential. Self-registration grants patient-level access only. "
                "Staff credentials are independently managed and audited."
            )
