
# pF9az7g4U2VVVcbU supabase db password
import streamlit_authenticator as stauth

plain_password = "1e1e1e1e"
hasher = stauth.Hasher()
hashed_password = hasher.hash(plain_password)
print(hashed_password)

