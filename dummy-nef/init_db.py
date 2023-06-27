# from session import async_db
# from api.config import conf

# from schemas.user import UserCreate

# def init_db(db: async_db) -> None:

#     collection = db["users"]
#     user = collection.find_one({'email': conf.FIRST_SUPERUSER})
#     #user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
#     if not user:
#         user_in = UserCreate(
#             email=conf.FIRST_SUPERUSER,
#             password=conf.FIRST_SUPERUSER_PASSWORD,
#             is_superuser=True,
#         )
#         result = collection.insert_one(user_in.__dict__)
#         print("Super user added: "+str(result.inserted_id))
#         #user = crud.user.create(db, obj_in=user_in)  # noqa: F841
#     else:
#         print("Super user already in database")

#     user = collection.find_one({'email': 'user@it.ua.pt'})
#     #user = crud.user.get_by_email(db, email='user@my-email.com')
#     if not user:
#         user_in = UserCreate(
#             email='user@it.ua.pt',
#             password='pass',
#             is_superuser=False,
#         )
#         result = collection.insert_one(user_in.__dict__)
#         print("User added: "+str(result.inserted_id))
#         #user = crud.user.create(db, obj_in=user_in) 
#     else:
#         print("User already in database")