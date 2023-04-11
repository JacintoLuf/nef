from session import static_client
from api.config import settings

from schemas.user import UserCreate

def init_db(db: static_client) -> None:

    collection = db["users"]
    user = collection.find_one({'email': settings.FIRST_SUPERUSER})
    #user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        result = collection.insert_one(user_in.__dict__)
        print("Super user added: "+result.inserted_id)
        #user = crud.user.create(db, obj_in=user_in)  # noqa: F841
    else:
        print("Super user already in database")

    user = collection.find_one({'email': 'user@it.ua.pt'})
    #user = crud.user.get_by_email(db, email='user@my-email.com')
    if not user:
        user_in = UserCreate(
            email='user@it.ua.pt',
            password='pass',
            is_superuser=False,
        )
        result = collection.insert_one(user_in.__dict__)
        print("User added: "+result.inserted_id)
        #user = crud.user.create(db, obj_in=user_in) 
    else:
        print("User already in database")