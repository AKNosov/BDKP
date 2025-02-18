import streamlit as st
import psycopg2
import hashlib
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "db",
    "database": "postgre",
    "user": "postgre",
    "password": "postgre",
    "port": "5432",
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.soldier = None
    st.session_state.rank = None
    st.session_state.sqcom = None
    st.session_state.soldreq = {}  
    
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_squads():
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT SquadID FROM Squad")
            squads = cur.fetchall()
            sq = []
            for s in squads:
                sq.append(s["squadid"])
            return sq
    except Exception as e:
        st.error(f"Ошибка при получении отрядов: {e}")
        return False
    finally:
        conn.close()
        
def main():
    if not st.session_state.logged_in:
        st.title("Здравия желаю!")
        st.subheader("Вход или регистрация")

        tab_login, tab_register = st.tabs(["Вход", "Регистрация"])
        with tab_login:
            fio = st.text_input("ФИО")
            password = st.text_input("Пароль", type="password")
            if st.button("Войти"):
                if login(fio, password):
                    pass
                    st.rerun()
                else:
                    st.error("Неверные данные для входа")

        with tab_register:
            fio = st.text_input("ФИО", key='nicecock')
            password = st.text_input("Пароль", type="password", key='bigdick')
            password_2 = st.text_input("Повторите пароль", type="password")
            birthdate = st.date_input("Дата рождения")
            sq = get_squads()
            sq_sel = st.selectbox(f"Выберите отряд", sq)
            rank = {"Рядовой": 2, "Сержант": 1}
            rank_select = st.selectbox("Звание:", list(rank.keys()))
            if st.button("Зарегистрироваться"):
                if not fio or not birthdate or not password or not password_2:
                    st.error("Все поля должны быть заполнены.")
                    return
                if password != password_2:
                    st.error("Ваши пароли не совпадают")
                    return
                if register(fio, password, rank[rank_select], sq_sel, birthdate):
                    st.success("Регистрация успешна. Войдите в систему.")
                else:
                    st.error("Ошибка регистрации")
    else:
        rank = st.session_state.rank
        st.sidebar.title("Навигация")
        if rank == 1 and st.session_state.sqcom != None:
            page = st.sidebar.selectbox("Страницы", ["Припасы", "Создать запрос", "Запросы", "Запасы", "Отряд", "Профиль"])
        elif rank == 2:
            page = st.sidebar.selectbox("Страницы", ["Припасы", "Создать запрос", "Запросы", "Запасы", "Профиль"])
        elif rank == 0:
            page = st.sidebar.selectbox("Страницы", ["Припасы", "Запросы", "Запасы", "Отряды", "Добавить припасы", "Профиль"])
        st.sidebar.button("Выйти", on_click=lambda: st.session_state.update({"logged_in": False, "soldier": None}))

        if page == "Припасы":
            view_supply(rank)
        elif page == "Создать запрос":
            view_soldreq()
        elif page == "Запросы":
            view_req(rank)
        elif page == "Запасы":
            view_res(rank)
        elif page == "Отряд" or page == "Отряды":
            view_squad(rank)
        elif page == "Добавить припасы":
            add_supply()
        elif page == "Профиль":
            view_account()
   
def login(fio, password):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            password1 = hash_password(password)
            cur.execute("""
                SELECT * FROM Soldier
                WHERE fio = %s AND passwordhash = %s
            """, (fio, password1))
            soldier = cur.fetchone()
            if soldier:
                st.session_state.logged_in = True
                st.session_state.soldier = soldier
                st.session_state.rank = soldier["rank"]
                if soldier["rank"] == 1:
                        cur.execute("""
                            SELECT * FROM squad 
                            WHERE squadcomanderid = %s
                        """, (soldier["soldierid"],))
                        st.session_state.sqcom = cur.fetchone()
                return True
            else:
                return False
    except Exception as e:
        st.error(f"Ошибка при входе: {e}")
        return False
    finally:
        conn.close()

def register(fio, password, rank, squadid, birthdate):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            password1 = hash_password(password)
            cur.execute("""
                INSERT INTO Soldier (fio, passwordhash, rank, squadid, birthdate)
                VALUES (%s, %s, %s, %s, %s)
            """, (fio, password1, rank, squadid, birthdate))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Ошибка при регистрации: {e}")
        return False
    finally:
        conn.close()

def update_profile(soldierid, fio, birthdate):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE soldier
                SET fio = %s, birthdate = %s
                WHERE soldierid = %s
            """, (fio, birthdate, soldierid))
            conn.commit()
            st.success("Профиль обновлен.")
    except Exception as e:
        st.error(f"Ошибка обновления профиля: {e}")
    finally:
        conn.close()

def view_account():
    st.title("Профиль")
    soldier = st.session_state.soldier
    fio = st.text_input("ФИО", value=soldier["fio"])
    birthdate = st.text_input("Дата рождения", value=soldier["birthdate"])
    if st.button("Обновить"):
        update_profile(soldier["soldierid"], fio, birthdate)

def add_to_soldreq(unit, quantity):
    if "soldreq" not in st.session_state:
        st.session_state.soldreq = {}

    supply_id = unit["supplyid"]
    if supply_id in st.session_state.soldreq:
        st.session_state.soldreq[supply_id]["quantity"] += quantity
    else:
        st.session_state.soldreq[supply_id] = {
            "name": unit["supname"],
            "weight": unit["supweight"],
            "quantity": quantity,
        }

def view_soldreq():
    st.title("Создать запрос")
    soldreq = st.session_state.soldreq
    if soldreq:
        total = 0
        for item in soldreq.values():
            st.write(f"{item['name']}: {item['quantity']} шт. x {item['weight']} кг")

            total = item['quantity'] * item['weight']
        st.write(f"Общий вес: {total} кг")
        if st.button("Оформить запрос"):
            if create_req(st.session_state.soldier["soldierid"], soldreq, total):
                st.session_state.soldreq = {}
    else:
        st.write("Запрос пуст.")

def create_req(soldier_id, soldreq, total):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO request (soldierid, reqdate, reqstatus, totalweight)
            VALUES (%s, NOW(), 'Обрабатывается', %s) RETURNING reqid
            """, (soldier_id, total))
            req_id = cur.fetchone()[0]
            for supply_id, item in soldreq.items():
                cur.execute("""
                    INSERT INTO reqdet (supplyid, reqid, amount)
                    VALUES (%s, %s, %s) 
                """, (supply_id, req_id, item["quantity"]))
            conn.commit()
            st.success("Запрос успешно оформлен!")
            return True
    except Exception as e:
        conn.rollback() 
        st.error(f"Ошибка оформления запроса: {e}")
        return False
    finally:
        conn.close()

def view_res(rank):
    st.title("Запасы")
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            soldier_id = st.session_state.soldier["soldierid"]
            cur.execute("""SELECT resid FROM reserve WHERE soldierid = %s""", (soldier_id,))
            res = cur.fetchall()
            if not res:
                st.write("У вас нет запасов.")
            for re in res:
                cur.execute("""SELECT supname, amount FROM ResSupplyView WHERE resid = %s""", (re['resid'],))
                un = cur.fetchone()  
                new_amount = st.number_input(f"Количество для {un['supname']}", value=un['amount'], min_value=0, max_value=un['amount'],
                        key=f"amount_{un['supname']}")
                if st.button("Удалить",
                        key=f"delete_{un['supname']}"):   
                    cur.execute("DELETE FROM reserve WHERE resid = %s", (re['resid'],))
                    conn.commit()
                    st.success("Запас успешно удалён")
                    st.rerun()
                if st.button("Изменить",
                        key=f"change_{un['supname']}"):
                    cur.execute("""
                        UPDATE reserve
                        SET amount = %s
                        WHERE resid = %s
                    """, (new_amount, re['resid']))
                    conn.commit()
                    st.success("Запас успешно изменён")
                    st.rerun()
    except Exception as e:
        st.error(f"Ошибка загрузки запасов: {e}")
    finally:
        conn.close()

def update_supply(supply_id, name, weight, stock_quantity, desc):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE supply
                SET supname = %s, supweight = %s, stockquantity = %s, supdescription = %s
                WHERE supplyid = %s
            """, (name, weight, stock_quantity, desc, supply_id))
            conn.commit()
    except Exception as e:
        st.error(f"Ошибка обновления припаса: {e}")
    finally:
        conn.close()

def view_supply(rank):
    st.title("Припасы")
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM types")
            types = cur.fetchall()
        search_query = st.text_input("Поиск", placeholder="Введите название...")
        type_options = {}
        type_options["Все категории"] = None
        for type in types:
            type_options[type["typename"]] = type["typeid"]
        selected_type = st.selectbox("Выберите категорию", list(type_options.keys()))
        query = "SELECT * FROM supply WHERE 1=1"
        params = []
        if search_query:
            query += " AND LOWER(supname) LIKE %s"
            params.append(f"%{search_query.lower()}%")
        if type_options[selected_type]:
            query += " AND typeid = %s"
            params.append(type_options[selected_type])
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            supply = cur.fetchall()
        for unit in supply:
            st.write(f"**{unit['supname']}** - {unit['supweight']} кг")
            st.write(f"Описание: {unit['supdescription']}")
            st.write(f"На складе: {unit['stockquantity']} шт.")
            if rank == 0:  
                if "editing" not in st.session_state:
                    st.session_state.editing = None

                if st.button("Редактировать", key=f"edit_{unit['supplyid']}"):
                    st.session_state.editing = unit['supplyid']
                    st.session_state.new_name = unit['supname']
                    st.session_state.new_weight = float(unit['supweight'])
                    st.session_state.new_desc = unit['supdescription']
                    st.session_state.new_stock = int(unit['stockquantity'])

                if st.session_state.editing == unit['supplyid']:
                    new_name = st.text_input("Название", value=st.session_state.new_name,
                                             key=f"name_{unit['supplyid']}")
                    new_weight = st.number_input(
                        "Вес", value=st.session_state.new_weight, min_value=0.0, key=f"weight_{unit['supplyid']}"
                    )
                    new_stock = st.number_input(
                        "Количество на складе", value=st.session_state.new_stock, min_value=0,
                        key=f"stock_{unit['supplyid']}"
                    )
                    new_desc = st.text_input(
                        "Описание", value=st.session_state.new_desc,
                        key=f"desc_{unit['supdescription']}"
                    )
                    st.session_state.new_name = new_name
                    st.session_state.new_weight = new_weight
                    st.session_state.new_stock = new_stock
                    st.session_state.new_desc = new_desc
                    if st.button("Сохранить изменения", key=f"save_{unit['supplyid']}"):
                        update_supply(unit['supplyid'], new_name, new_weight, new_stock, new_desc)
                        st.session_state.editing = None
                        st.rerun()
            else: 
                quantity = st.number_input(
                    f"Количество для {unit['supname']}", min_value=1, max_value=unit['stockquantity'], step=1,
                    key=f"qty_{unit['supplyid']}"
                )
                if st.button("Добавить в запрос", key=f"add_{unit['supplyid']}"):
                    add_to_soldreq(unit, quantity)
                    st.success(f"{unit['supname']} добавлен в запрос")
    except Exception as e:
        st.error(f"Ошибка загрузки товаров: {e}")
    finally:
        conn.close()

def add_supply():
    st.title("Добавить припасы")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT typeid, typename FROM types")
            types = cur.fetchall()
            type_options = {t['typename']: t['typeid'] for t in types}
            supply_name = st.text_input("Название припаса")
            supply_description = st.text_input("Описание припаса")
            supply_weight = st.number_input("Вес", min_value=0.0, step=0.01)
            supply_stock = st.number_input("Количество на складе", min_value=0, step=1)
            selected_type = st.selectbox("Тип", list(type_options.keys()))
            if st.button("Добавить припас"):
                if supply_name.strip():
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO supply (supname, supdescription, supweight, stockquantity, typeid)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (supply_name, supply_description, supply_weight, supply_stock, type_options[selected_type]),
                            )
                            conn.commit()
                            st.success(f"Припас '{supply_name}' успешно добавлен!")
                    except Exception as e:
                        st.error(f"Ошибка при добавлении припаса: {e}")
                else:
                    st.error("Название припаса не может быть пустым.")
    except Exception as e:
        st.error(f"Ошибка при загрузке категорий: {e}")
    finally:
        conn.close()

def view_req(rank):
    st.title("Запросы")
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if rank == 0 or (rank == 1 and st.session_state.sqcom != None): 
                if rank == 0:
                    search_query = st.text_input("Поиск по солдату", placeholder="Введите ФИО солдата...")
                    cur.execute("""SELECT * FROM request WHERE SoldierID=(SELECT soldierid FROM Soldier WHERE fio = %s)""", (search_query, ))
                if rank == 1:
                    cur.execute("""SELECT fio, soldierid FROM soldier WHERE SquadID=%s""", (st.session_state.sqcom['squadid'],))
                    t = cur.fetchall()
                    n = {}
                    for i in t:
                        n[i['fio']] = i['soldierid']
                    search_query = st.selectbox (f"Выберите солдата", list(n.keys()))
                    cur.execute("""SELECT * FROM request WHERE SoldierID=%s""", (n[search_query],))
                requests = cur.fetchall()
                if not requests:
                    st.write("Нет запросов в системе.")
                for req in requests:
                    st.write(f"**Запрос №{req['reqid']}** - Статус: {req['reqstatus']}")
                    st.write(f"Дата: {req['reqdate']} - Вес: {req['totalweight']} кг")
                    cur.execute("""SELECT supname, amount FROM ReqDetSupplyView WHERE reqID = %s""", (req['reqid'],))
                    reqname = cur.fetchall()
                    for r in reqname:
                        st.write(f"Название: {r['supname']} | Количество: {r['amount']}")
                    if req['reqstatus'] == "Обрабатывается" and rank == 0:      
                        new_status = st.selectbox(f"Изменить статус запроса №{req['reqid']}",
                                                ["Одобрен", "Отклонён"],
                                                key=f"status_{req['reqid']}")
                        if st.button(f"Изменить", key=f"update_{req['reqid']}"):
                            cur.execute("""
                                UPDATE request
                                SET reqStatus = %s
                                WHERE reqID = %s
                            """, (new_status, req['reqid']))
                            conn.commit()
                            cur.execute("""
                                CALL ReqApply(%s)
                            """, (req['reqid'], ))
                            conn.commit()
                            st.success(f"Статус запроса №{req['reqid']} обновлён на '{new_status}'")

            else:  
                soldier_id = st.session_state.soldier["soldierid"]
                cur.execute(f"SELECT * FROM request WHERE SoldierID={soldier_id}")
                requests = cur.fetchall()
                if not requests:
                    st.write("Нет запросов в системе.")
                for req in requests:
                    st.write(f"**Запрос №{req['reqid']}** - Статус: {req['reqstatus']}")
                    st.write(f"Дата: {req['reqdate']} - Вес: {req['totalweight']} кг")
                    cur.execute(f"SELECT supname, amount FROM ReqDetSupplyView WHERE reqID={req['reqid']}")
                    reqname = cur.fetchall()
                    for r in reqname:
                        st.write(f"Название: {r['supname']} | Количество: {r['amount']}")
    except Exception as e:
        st.error(f"Ошибка загрузки запросов: {e}")
    finally:
        conn.close()

def update_squad(squadid, soldierid):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE soldier SET squadid = %s WHERE soldierid = %s""", (squadid, soldierid))
            conn.commit()
            st.success("Отряд успешно сменён")
    except Exception as e:
        st.error(f"Ошибка смены отряда: {e}")
    finally:
        conn.close()

def change_com(sqcom, sqid):
    conn = get_db_connection()
    if not conn:
        return
    try: 
        with conn.cursor() as cur:
            cur.execute("""UPDATE squad SET squadcomanderid = %s WHERE squadid = %s""", 
                        (sqcom, sqid))
            conn.commit()
            st.success("Командир успешно сменён")
    except Exception as e:
        st.error(f"Ошибка смены командира: {e}")
    finally:
        conn.close()


def view_squad(rank):
    st.title(f"Отряд №{st.session_state.sqcom['squadid']}" if rank == 1 else "Отряды")
    r = {0: "Лейтенант", 1: "Рядовой", 2: "Сержант"}
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if rank == 0: 
                cur.execute("SELECT * FROM squad")
                squads = cur.fetchall()
                a = []
                for i in squads:
                    a.append(i['squadid'])
                search_query = st.selectbox (f"Выберите отряд", a)
                cur.execute("""SELECT soldierid, fio, rank, birthdate FROM soldier WHERE squadid = %s""", (search_query,))                
                sq = cur.fetchall()
                st.write("Солдаты:")
                if "change" not in st.session_state:
                    st.session_state.change = None
                for sol in sq:
                    st.write(f"ФИО: {sol['fio']} | Звание: {r[sol['rank']]} | Дата рождения: {sol['birthdate']}") 
                    if st.button("Удалить",
                        key=f"s_{sol['fio']}"):
                        if st.session_state.soldier['soldierid'] != sol['soldierid']:
                            cur.execute("""DELETE FROM soldier WHERE soldierid = %s""", (sol['soldierid'],))
                            conn.commit()
                            st.success("Солдат успешно удалён")
                        else: st.write("Невозможно удалить себя!")
                    if st.button("Сменить отряд", key=f"d_{sol['fio']}"):
                        st.session_state.change = sol['soldierid']
                        st.session_state.new_sq = search_query
                    if st.session_state.change == sol['soldierid']:
                        search_q = st.selectbox (f"Выберите отряд", a, key=f"m_{sol['fio']}")
                        st.session_state.new_sq = search_q
                        if st.button("Подтвердить", key=f"q_{sol['fio']}"):
                            update_squad(search_q, sol['soldierid'])
                            st.session_state.change = None
                    cur.execute("""SELECT resid FROM reserve WHERE soldierid = %s""", (sol['soldierid'],))
                    res = cur.fetchall()
                    if not res:
                        st.write("Нет запасов.")
                    else: st.write("Запасы") 
                    for re in res:
                        cur.execute("""SELECT supname, amount FROM ResSupplyView WHERE resid = %s""", (re['resid'],))
                        un = cur.fetchone() 
                        st.write(f"Количество для {un['supname']}: {un['amount']}")
                st.write("Командир:")
                cur.execute("""SELECT s.fio, s.birthdate
                            FROM squad sq
                            JOIN soldier s ON sq.squadcomanderid = s.soldierid
                            WHERE sq.squadid = %s""", (search_query, ))
                com = cur.fetchone()
                st.write(f"ФИО: {com['fio']} | Дата рождения: {com['birthdate']}") 
                if st.button("Сменить"):
                    st.session_state.change = com['fio']
                    st.session_state.serj = com['fio']
                if st.session_state.change == com['fio']:
                    cur.execute("""SELECT fio, soldierid FROM soldier WHERE rank = 1 AND squadid = %s""", (search_query,))
                    m = cur.fetchall()
                    b = {}
                    for i in m:
                        b[i['fio']] = i['soldierid']
                    s_query = st.selectbox (f"Выберите из сержантов отряда", b.keys())
                    st.session_serj = s_query
                    if st.button("Подтвердить"):
                        change_com(b[s_query], search_query)
                        st.session_state.change = None
            else:  
                sq = st.session_state.sqcom
                st.write("Солдаты:")
                cur.execute("""SELECT soldierid, fio, rank, birthdate FROM soldier WHERE squadid = %s""", (sq['squadid'],))
                s = cur.fetchall()
                for sol in s:
                    st.write(f"ФИО: {sol['fio']} | Звание: {r[sol['rank']]} | Дата рождения: {sol['birthdate']}") 
                    if st.button("Удалить",
                        key=f"s_{sol['fio']}"):
                        if st.session_state.soldier['soldierid'] != sol['soldierid']:
                            cur.execute("""DELETE FROM soldier WHERE soldierid = %s""", (sol['soldierid'],))
                            conn.commit()
                            st.success("Солдат успешно удалён")
                        else: st.write("Невозможно удалить себя!")
                    cur.execute("""SELECT resid FROM reserve WHERE soldierid = %s""", (sol['soldierid'],))
                    res = cur.fetchall()
                    if not res:
                        st.write("Нет запасов.")
                    else: st.write("Запасы") 
                    for re in res:
                        cur.execute("""SELECT supname, amount FROM ResSupplyView WHERE resid = %s""", (re['resid'],))
                        un = cur.fetchone()  
                        st.write(f"Количество для {un['supname']}: {un['amount']}")
    except Exception as e:
        st.error(f"Ошибка загрузки отрядов: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()