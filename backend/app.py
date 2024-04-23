import datetime
import random
from fastapi import FastAPI
from .database import create_supabase_client

app = FastAPI()
supabase = create_supabase_client()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/generate")
async def generate():
    """
    Generate Random Workout and Set Data
    """
    generated_data = {}

    for i in range(100):
        uid = random.randint(1,2)
        date = datetime.datetime.now().date().strftime("%Y/%m/%d")
        eid = random.randint(1,2)
        reps = random.randint(8,12)
        weight = round(random.uniform(20,80), 2)

        sid = await insert_sets(
            reps=reps,
            weight=weight
        )
        
        await insert_workouts(
            uid=uid,
            date=date,
            eid=eid,
            sid=sid
        )

        generated_data[i] = {
            "uid": uid,
            "date": date,
            "eid": eid,
            "sid": sid,
            "reps": reps,
            "weight": weight
        }
    
    return {"Generated Data": generated_data}
    
    
# ---------- WORKOUTS ----------

@app.post("/insert_workouts")
async def insert_workouts(
    uid: int,
    date: str,
    eid: int,
    sid: int
) -> dict:
    """
    Insert New record into the Workouts Table

    Args:
        uid: User ID
        date: Date in format %Y/%m/%d
        eid: Exercise ID
        sid: Set ID
    """
    try:
        supabase.from_("workouts")\
        .insert({"uid":uid,
                "date": date,
                "eid": eid,
                "sid": sid})\
        .execute()

        return {"Inserted Workout": {
            "uid":uid, 
            "date": date,
            "eid": eid,
            "sid": sid}
            }
    
    except Exception as e:
        print(e)
        return None
    
@app.get("/get_workouts")
async def get_workouts(
    uid: int,
    date: str

) -> dict:
    """
    Gets all workouts records for a given user and date.

    Args:
        uid: ID of user
        date: Format %Y/%m/%d, used as query parameter

    Returns: Dict  
    """

    try:
        workouts_json = {}

        # Get all workout records
        workouts = supabase.from_("workouts")\
        .select("*")\
        .eq(column="uid", value=uid)\
        .eq(column="date", value=date)\
        .order(column="id", desc=True)\
        .execute().data

        eids = set([i['eid'] for i in workouts])

        for eid in eids:
            workouts_json[eid] = {}
            exercise_data = supabase.from_("exercises")\
            .select("*")\
            .eq(column="id", value=eid)\
            .limit(size=1)\
            .execute().data[0]

            workouts_json[eid]['name'] = exercise_data['name']
            workouts_json[eid]['muscle_group'] = exercise_data['muscle_group']
            workouts_json[eid]['icon'] = exercise_data['icon']
            workouts_json[eid]['sets'] = {}

            # Fetch related sets
            sets = supabase.from_("workouts")\
            .select("sid")\
            .eq(column='date', value=date)\
            .eq(column='eid', value=eid)\
            .execute().data
            
            sids = [j['sid'] for j in sets]
            set_data = await get_all_sets(sids)
            
            for i in set_data:
                print(i)
                sid = i['id']
                reps = i['reps']
                weight = i['weight']
                
                workouts_json[eid]['sets'][sid] = {}
                workouts_json[eid]['sets'][sid]['reps'] = reps
                workouts_json[eid]['sets'][sid]['weight'] = weight

        return workouts_json
    
    except Exception as e:
        print(e)
        raise

# ---------- SETS ----------

@app.post("/insert_sets")
async def insert_sets(
    reps: int,
    weight: float,
) -> int:
    """
    Insert New record into the Sets Table

    Args:
        reps: Integer of Reps performed
        weight: Float of the weight used

    Returns:
        ID of the latest inserted recored from the table "sets"
    """

    try:
        supabase.from_("sets")\
        .insert({"reps":reps,
                "weight": round(weight,2)
                })\
        .execute()

        sid = supabase.from_("sets")\
        .select("id")\
        .order(column="id", desc=True)\
        .limit(size=1)\
        .execute()

        sid = int(sid.data[0]['id'])
        return sid
    
    except Exception as e:
        print(e)
        return None
    
@app.put("/update_sets")
async def update_sets(
    sid: int,
    reps: int,
    weight: float

) -> bool:
    """
    Update record in the Sets Table

    Args:
        sid: ID of the set record,
        reps: Integer of Reps performed
        weight: Float of the weight used

    Returns: None
    """

    try:
        supabase.from_("sets")\
        .update({"reps":reps,
                "weight":weight})\
        .eq(column="id", value=sid)\
        .execute()

        return True
    
    except Exception as e:
        print(e)
        return False
    
@app.get("/get_sets")
async def get_sets(
    sid: int

) -> dict:
    """
    Gets record in the Sets Table

    Args:
        sid: ID of the set record

    Returns: Dict
    """

    try:
        data = supabase.from_("sets")\
        .select("*")\
        .eq(column="id", value=sid)\
        .execute().data[0]

        return data
    
    except Exception as e:
        print(e)
        return None
    
@app.get("/get_all_sets")
async def get_all_sets(
    sids: list
) -> list:
    """
    Gets record in the Sets Table

    Args:
        sid: list of set ID's

    Returns: Dict
    """

    try:
        data = supabase.from_("sets")\
        .select("*")\
        .in_(column="id", values=sids)\
        .execute().data

        return data
    
    except Exception as e:
        print(e)
        raise
    
@app.delete("/delete_sets")
async def delete_sets(
    sid: int

) -> bool:
    """
    Delets record in the Sets Table

    Args:
        sid: ID of the set record

    Returns: Dict
    """

    try:
        supabase.from_("sets")\
        .delete()\
        .eq(column="id", value=sid)\
        .execute()

        supabase.from_("workouts")\
        .delete()\
        .eq(column="sid", value=sid)\
        .execute()

        return True
    
    except Exception as e:
        print(e)
        return False  


# ---------- USERS ----------
@app.post("/insert_users")
async def insert_users(
    firstname: str,
    lastname: str,
    dob: str = None

) -> bool:
    """
    Insert New record into the Users Table

    Args:
        firstname: Firstname of user
        lastname: Lastname of user
        dob: Date of Birth of user. Default = None

    Returns: None
    """

    try:
        supabase.from_("users")\
        .insert({"firstname":firstname,
                "lastname":lastname,
                "dob":dob})\
        .execute()

        return True
    
    except Exception as e:
        print(e)
        return False

@app.put("/update_users")
async def update_users(
    id: int,
    firstname: str,
    lastname: str,
    dob: str

) -> bool:
    """
    Update record in the Users Table

    Args:
        id: id of user
        firstname: Firstname of user
        lastname: Lastname of user
        dob: Date of Birth of user

    Returns: None
    """

    try:
        supabase.from_("users")\
        .update({"firstname":firstname,
                "lastname":lastname,
                "dob":dob})\
        .eq(column="id", value=id)\
        .execute()

        return True
    
    except Exception as e:
        print(e)
        return False
    
@app.get("/get_users")
async def get_users(
    id: int

) -> dict:
    """
    Gets record in the Users Table

    Args:
        id: id of user

    Returns: Dict
    """

    try:
        data = supabase.from_("users")\
        .select("*")\
        .eq(column="id", value=id)\
        .execute().data[0]

        return data
    
    except Exception as e:
        print(e)
        return None