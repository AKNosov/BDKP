from datetime import datetime
import streamlit as st
import psycopg2
import os
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
            return psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgre"),
            user=os.getenv("POSTGRES_USER", "postgre"),
            password=os.getenv("POSTGRES_PASSWORD", "postgre"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.soldier = None
    st.session_state.rank = None
    st.session_state.sqcom = None
    st.session_state.soldreq = {}  
    
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
            view_squad()
        elif page == "Добавить припасы":
            add_supply()
        elif page == "Профиль":
            view_account()
   
def get_squads():
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor as cur:
            cur.execute("SELECT SquadID FROM Squad")
            squads = cur.fetchall()
            return squads
    except Exception as e:
        st.error(f"Ошибка при получении отрядов: {e}")
        return False
    finally:
        conn.close()

def login(fio, password):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM Soldier
                WHERE fio = %s AND passwordhash = crypt(%s, passwordhash)
            """, (fio, password))
            soldier = cur.fetchone()
            if soldier:
                st.session_state.logged_in = True
                st.session_state.soldier = soldier
                st.session_state.rank = soldier["rank"]
                if soldier["rank"] == 1:
                        cur.execute("""
                            SELECT * FROM squad 
                            WHERE squadcomanderid = %s
                        """, (soldier["soldierid"]))
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
            cur.execute("""
                INSERT INTO Soldier (fio, passwordhash, rank, squadid, birthdate)
                VALUES (%s, crypt(%s, gen_salt('bf')), %s, %s, %s)
            """, (fio, password, rank, squadid, birthdate))
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
            query += " AND (LOWER(name) LIKE %s or LOWER(name) LIKE fix_mistake_search(%s))"
            params.append(f"%{search_query.lower()}%")
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

                if st.button("Удалить", key=f"delete_{unit['supplyid']}"):
                    delete_supply(unit['supplyid'])
                    st.rerun()

                if st.button("Редактировать", key=f"edit_{unit['supplyid']}"):
                    st.session_state.editing = unit['supplyid']
                    st.session_state.new_name = unit['supname']
                    st.session_state.new_weight = float(unit['supweight'])
                    st.session_state.new_stock = int(unit['stockquantity'])

                if st.session_state.editing == unit['supplyid']:
                    new_name = st.text_input("Название", value=st.session_state.new_name,
                                             key=f"name_{unit['supplyid']}")
                    new_weight = st.number_input(
                        "Вес", value=st.session_state.new_weight, min_value=0.0, key=f"price_{unit['supplyid']}"
                    )
                    new_stock = st.number_input(
                        "Количество на складе", value=st.session_state.new_stock, min_value=0,
                        key=f"stock_{unit['supplyid']}"
                    )
                    st.session_state.new_name = new_name
                    st.session_state.new_weight = new_weight
                    st.session_state.new_stock = new_stock
                    if st.button("Сохранить изменения", key=f"save_{unit['supplyid']}"):
                        update_supply(unit['supplyid'], new_name, new_weight, new_stock)
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

def delete_supply(supply_id):
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM supply WHERE supplyid = %s", (supply_id,))
            conn.commit()
            st.success("Припас успешно удалён")
    except Exception as e:
        st.error(f"Ошибка удаления припаса: {e}")
    finally:
        conn.close()

def update_supply(supply_id, name, weight, stock_quantity):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE supply
                SET supname = %s, supweight = %s, stockquantity = %s
                WHERE supplyid = %s
            """, (name, weight, stock_quantity, supply_id))
            conn.commit()
            st.success("Припас успешно обновлен")
    except Exception as e:
        st.error(f"Ошибка обновления припаса: {e}")
    finally:
        conn.close()

def add_to_soldreq(unit, quantity):
    if "soldreq" not in st.session_state:
        st.session_state.soldreq = {}

    supply_id = unit["supplyid"]
    if supply_id in st.session_state.soldreq:
        st.session_state.soldreq[supply_id]["quantity"] += quantity
    else:
        st.session_state.cart[supply_id] = {
            "name": unit["supname"],
            "weight": unit["supweight"],
            "quantity": quantity,
        }

def view_soldreq():
    st.title("Создать запрос")
    soldreq = st.session_state.soldreq
    if soldreq:
        total = 0
        for item in soldreq:
            st.write(f"{item['name']}: {item['quantity']} шт. x {item['weight']} кг")
            total = item['quantity'] * item['weight']
        st.write(f"Общий вес: {total} кг")
        if st.button("Оформить запрос"):
            if create_req(st.session_state.soldier["soldierid"], soldreq, total):
                st.session_state.soldreq = {}
                st.rerun()
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
                    VALUES (%s, %s) 
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
                                VALUES (%s, %s, %s, %s)
                                """,
                                (supply_name, supply_description, supply_weight, supply_stock, type_options[selected_type]),
                            )
                            conn.commit()
                            st.success(f"Припас '{supply_name}' успешно добавлен!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при добавлении припаса: {e}")
                else:
                    st.error("Название припаса не может быть пустым.")
    except Exception as e:
        st.error(f"Ошибка при загрузке категорий: {e}")
    finally:
        conn.close()

def view_res(rank):
    st.title("Запасы")
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor as cur:
            soldier_id = st.session_state.soldier["soldierid"]
            cur.execute("SELECT resid FROM reserve WHERE soldierid = %s", (soldier_id,))
            res = cur.fetchall()
            if not res:
                st.write("У вас нет запасов.")
            res_dict = {}
            for re in res:
                cur.execute("SELECT supplyid, amount FROM reserve WHERE resid = %s", (re))
                resname = cur.fetchone()
                cur.execute("SELECT supname FROM supply WHERE supplyid = %s", (resname['supplyid']))
                supname = cur.fetchone()
                res_dict[re] = {
                    "name": supname,
                    "amount": resname['amount'],
                }
            for k, unit in res_dict.items():
                new_amount = st.number_input(f"Количество для {unit['name']}", value=unit['amount'], min_value=0, max_value=unit['amount'],
                        key=f"amount_{k}")
                if st.button("Удалить"):   
                    cur.execute("DELETE FROM reserve WHERE resid = %s", (k))
                    conn.commit()
                    st.success("Запас успешно удалён")
                    st.rerun()
                if st.button("Изменить"):
                    cur.execute("""
                        UPDATE reserve
                        SET amount = %s
                        WHERE supplyid = %s
                    """, (new_amount, k))
                    conn.commit()
                    st.success("Запас успешно изменён")
                    st.rerun()
    except Exception as e:
        st.error(f"Ошибка загрузки запасов: {e}")
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
                    cur.execute(f"SELECT * FROM request WHERE SoldierID={search_query}")
                if rank == 1:
                    cur.execute(f"SELECT fio, soldierid FROM soldier WHERE SquadID={st.session_state.sqcom['squadid']}")
                    t = cur.fetchall()
                    n = {i['fio']: i['soldierid'] for i in t}
                    search_query = st.selectbox (f"Выберите солдата", list(n['fio']))
                    cur.execute(f"SELECT * FROM request WHERE SoldierID={n[search_query]}")
                requests = cur.fetchall()
                if not requests:
                    st.write("Нет запросов в системе.")
                for req in requests:
                    st.write(f"**Запрос №{req['reqid']}** - Статус: {req['reqstatus']}")
                    st.write(f"Дата: {req['reqdate']} - Вес: {req['totalweight']} кг")
                    cur.execute(f"SELECT supplyid, amount FROM reqdet WHERE reqID={req['reqid']}")
                    reqname = cur.fetchall()
                    for r in reqname:
                        cur.execute("SELECT supname FROM supply WHERE supplyid = %s", (r['supplyid']))
                        supname = cur.fetchone()
                        st.write(
                            f"Припас: {supname} | Количество: {r['amount']}")
                            
                    new_status = st.selectbox(f"Изменить статус запроса №{req['reqid']}",
                                              ["Обрабатывается", "Одобрен", "Отклонён"],
                                              key=f"status_{req['reqid']}")
                    if st.button(f"Обновить статус запроса №{req['reqid']}", key=f"update_{req['reqid']}"):
                        cur.execute("""
                            UPDATE request
                            SET reqStatus = %s
                            WHERE reqID = %s
                        """, (new_status, req['reqid']))
                        conn.commit()
                        if new_status == "Одобрен":
                            for i in reqname:
                                cur.execute("""
                                    UPDATE supply
                                    SET stockquantity -= %s
                                    WHERE supplyid = %s
                                """, (i['amount'], i['supplyid']))
                                conn.commit()
                                cur.execute("""
                                    UPDATE reserve
                                    SET amount += %s
                                    WHERE soldierid = %s AND supplyid = %s
                                """, (i['amount'], search_query, i['supplyid']))
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
                    cur.execute(f"SELECT supplyid, amount FROM reqdet WHERE reqID={req['reqid']}")
                    reqname = cur.fetchall()
                    for r in reqname:
                        cur.execute("SELECT supname FROM supply WHERE supplyid = %s", (r['supplyid']))
                        supname = cur.fetchone()
                        st.write(
                            f"Припас: {supname} | Количество: {r['amount']}")
    except Exception as e:
        st.error(f"Ошибка загрузки заказов: {e}")
    finally:
        conn.close()

def view_squad(rank):
    st.title("Отряд" if rank == 1 else "Отряды")
    rank = {1: "Рядовой", 2: "Сержант"}
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if rank == 0: 
                cur.execute("SELECT * FROM squad")
                squads = cur.fetchall()
                search_query = st.selectbox (f"Выберите отряд", squads['squadid'])
                cur.execute("SELECT soldierid, fio, rank, birthdate FROM soldier WHERE squadid = %s", (search_query))                
                sq = cur.fetchall()
                st.write("Солдаты:")
                serj = {}
                for sol in sq:
                    if sol['rank'] == 1:
                        serj[sol['fio']] = sol['soldierid']
                    st.write(f"ФИО: {sol['fio']} | Звание: {rank[sol['rank']]} | Дата рождения: {sol['birthdate']}") 
                    if st.button("Удалить"):
                        cur.execute("DELETE FROM soldier WHERE soldierid = %s", (sol['soldierid']))
                        conn.commit()
                        st.success("Солдат успешно удалён")
                        st.rerun()
                    if st.button("Сменить отряд"):
                        search_q = st.selectbox (f"Выберите отряд", squads['squadid'])
                        cur.execute("UPDATE soldier SET squadid = %s WHERE soldierid = %s", (search_q, sol['soldierid']))
                        conn.commit()
                        st.success("Отряд успешно сменён")
                        st.rerun()
                st.write("Командир:")
                cur.execute("SELECT squadcommanderid FROM squad WHERE squadid = %s", (search_query))
                f = cur.fetchone()
                cur.execute("SELECT fio, birthdate FROM soldier WHERE soldierid = %s", (f))
                com = cur.fetchone()
                st.write(f"ФИО: {com['fio']} | Дата рождения: {com['birthdate']}") 
                if st.button("Сменить"):
                    if serj == None:
                        st.write("В отряде нет сержантов") 
                    else: 
                        s_query = st.selectbox (f"Выберите из сержантов отряда", serj.keys())
                        cur.execute("UPDATE squad SET squadcomanderid = %s WHERE squadid = %s", 
                                    (serj[s_query], search_query))
                        conn.commit()
                        st.success("Командир успешно сменён")
                        st.rerun()
            else:  
                sq = st.session_state.sqcom
                st.write("Солдаты:")
                cur.execute("SELECT soldierid, fio, rank, birthdate FROM soldier WHERE squadid = %s", (sq['squadid']))
                s = cur.fetchall()
                for sol in s:
                    st.write(f"ФИО: {sol['fio']} | Звание: {rank[sol['rank']]} | Дата рождения: {sol['birthdate']}") 
                    if st.button("Удалить"):
                        cur.execute("DELETE FROM soldier WHERE soldierid = %s", (sol['soldierid']))
                        conn.commit()
                        st.success("Солдат успешно удалён")
                        st.rerun()
    except Exception as e:
        st.error(f"Ошибка загрузки отрядов: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()