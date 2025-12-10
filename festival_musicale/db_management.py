import sqlite3
from datetime import datetime, timedelta

DB = 'database.db'


def log_error(e):
    with open('log.txt', 'a') as log:
        log.write(f'{e}\n')

def insert_user_in_db(name, surname, email, password_hash, username, user_type):
    with sqlite3.connect(DB) as db:
        try:
            sql = 'INSERT INTO users (name, surname, email, password, username, type) VALUES (?, ?, ?, ?, ?, ?)'
            cursor = db.cursor()
            cursor.execute(sql, (name, surname, email, password_hash, username, user_type))
            db.commit()
            return True
        except Exception as e:
            log_error(f'{e}')
            return False


def check_both_username_email(email, username):
    with sqlite3.connect(DB) as db:
        try:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            el = cursor.fetchone()
            if el:
                return 'mail already in db'
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            el2 = cursor.fetchone()
            if el2:
                return 'username already in db'
            return 'ok'
        except Exception as e:
            log_error(f'{e}\n')
            return 'error'


def retrieve_user(id):
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? OR username = ?', (id,id))
            element = cursor.fetchone()
            if element:
                element = dict(element)
                return element
            else:
                return None
        except Exception as e:
            log_error(f'{e}')
            return 'error'
        
def check_day(day):
    with sqlite3.connect(DB) as db:
       try:
            cursor = db.cursor()
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE firstDay = ?', (day,))
            firstDay = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE secondDay = ?', (day,))
            secondDay = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE thirdDay = ?', (day,))
            thirdDay = cursor.fetchone()[0] or 0

            total = firstDay + secondDay + thirdDay
            
        

            return total < 200
       except Exception as e:
           log_error(f'{e}')
           return False
       
def check_allowed_ticket(email):
    with sqlite3.connect(DB) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            try:
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                element = cursor.fetchone()
                
                if element is None:
                    log_error(f'Email non registrata: {email}')
                    return False

                if element["type"] == 'organizzatore' :
                    return False
                cursor.execute('SELECT mail FROM tickets WHERE mail = ?', (email,))
                allowed = cursor.fetchone()
                if allowed is None:
                    return True
                else:
                    log_error('ticket already bought')
                    return False
            except Exception as e:
                log_error(f'{e}')
                return False
                
def insert_ticket_into_db(email, ticketType, days):
    with sqlite3.connect(DB) as db:
        try:
            cursor = db.cursor()
            if len(days) == 1:
                cursor.execute(
                    'INSERT INTO tickets (mail, ticketType, firstDay) VALUES (?,?,?)',
                    (email, ticketType, days[0])
                )
            elif len(days) == 2:
                cursor.execute(
                    'INSERT INTO tickets (mail, ticketType, firstDay, secondDay) VALUES (?,?,?,?)',
                    (email, ticketType, days[0], days[1])
                )
            else:
                cursor.execute(
                    'INSERT INTO tickets (mail, ticketType, firstDay, secondDay, thirdDay) VALUES (?,?,?,?,?)',
                    (email, ticketType, days[0], days[1], days[2])
                )
            db.commit()
            return True
        except Exception as e:
            log_error(f'{e}')
            return False
        
def check_free_spot(stage,day,start,duration, idPerformance = None):
    with sqlite3.connect(DB) as db:
        try:
            sql = "SELECT * FROM performances WHERE day = ? AND stage = ? AND typePost = ?"
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute(sql, (day,stage, 'pubblicato'))
            raw = cursor.fetchall()
            concerts = [dict(row) for row in raw]
        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}') #restituisce un booleano per definire che non è andata a buon fine, più la spiegazione dell'errore
    if not concerts:
        return (True, '') #formato per la riuscita: un booleano e una stringa vuota (no messaggi)
    
    
    c_start = datetime.strptime(start, "%H:%M") #converto in oggetto ora la durata che sto controllando
    c_time = timedelta(minutes=int(duration))
    c_end = c_start+c_time

    for concert in concerts:

        if idPerformance is not None and int(concert["id"]) == int(idPerformance):
            continue

        h_start = datetime.strptime(concert["start"], "%H:%M")
        d_time = timedelta(minutes=int(concert["duration"]))
        e_start = h_start + d_time

        if c_start < e_start and c_end > h_start:
            return (False, 'Concerto sovrapposto ad uno gia pianificato per giornata e palco designati')
    
    return (True, '')

def insert_performance_into_db(artist, day, start, duration, stage, genre, image, description, typePost, creator):
    with sqlite3.connect(DB) as db:
        sql = "INSERT INTO performances (artist, day, start, duration, stage, genre, image, description, typePost, creator) VALUES (?,?,?,?,?,?,?,?,?,?)"
        cursor = db.cursor()
        try:
            cursor.execute(sql, (artist, day, start, duration, stage, genre, image, description, typePost, creator))
            db.commit()
            return True
        except Exception as e:
            log_error(f'{e}')
            return False

def retrieve_editable_performances(username):
    sql = "SELECT * FROM performances WHERE creator = ? AND typePost = ?"
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute(sql, (username, 'bozza'))
            raw_elements = cursor.fetchall()
        except Exception as e:
            log_error(f'{e}')
            return (False, f'e')
    if not raw_elements:
        log_error('no performances')
        return (True, 'no performances')
    elements = [dict(raw_element) for raw_element in raw_elements]
    log_error(f'{elements}')
    return (True, elements)   
    
def retrieve_ticket_info(email):
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute('SELECT * FROM tickets WHERE mail = ?', (email,))
            element = cursor.fetchone()
        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}')
    if element is None:
        return (True, 'no tickets found')
    else:
        return (True, dict(element))
    
def retrieve_performance(id):
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute('SELECT * FROM performances WHERE id = ?', (id,))
            element = cursor.fetchone()
            if element is None:
                return (True, 'no performance found')
            else:
                return (True, dict(element))

        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}')
        
def check_artist_integrity(artist, idPerformance = None):
    artist = artist.strip()
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        try:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM performances WHERE LOWER(artist) = LOWER(?) ', (artist,))
            performance = cursor.fetchall()
        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}')
    if not performance:
        return (True, '')
    else:
        if idPerformance is not None:
            performances = [dict(p) for p in performance]
            if int(performances[0]["id"]) == int(idPerformance) and len(performances) == 1:
                return(True, '')
            else:
                return (False, 'Performance non modificabile: artista già presente nel database')
        else:
            return (False, 'Performance non inseribile nel database: artista gia presente ne database')
            


def edit_performance(idPost, artist, day, start, duration, stage, genre, image, description, typePost):
    sql_file = "UPDATE performances SET artist = ?, day =?, start = ?, duration = ?, stage = ?, genre = ?, image = ?, description = ?, typePost = ? WHERE id = ?"
    sql_nofile = "UPDATE performances SET artist = ?, day =?, start = ?, duration = ?, stage = ?, genre = ?, description = ?, typePost = ?  WHERE id = ?"

    with sqlite3.connect(DB) as db:
        try:
            cursor = db.cursor()
            if image is None:
                cursor.execute(sql_nofile, (artist,day,start,duration, stage, genre, description, typePost, idPost))
            else:
                cursor.execute(sql_file,(artist,day,start,duration, stage, genre,image, description, typePost, idPost))
            db.commit()
            return (True,)
        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}')
        
def all_performances(published = False):
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            if published == True:
                cursor.execute('SELECT * FROM performances WHERE typePost = ?', ('pubblicato',))
            else:
                cursor.execute('SELECT * FROM performances')
            raws = cursor.fetchall()
            performances = [dict(raw) for raw in raws]
            return(True, performances)
        except Exception as e:
            log_error(f'{e}')
            return (False, f'{e}')

def delete_draft(idDraft):
    with sqlite3.connect(DB) as db:
        try:
            cursor = db.cursor()
            cursor.execute('DELETE FROM performances WHERE id = ? AND typePost = ?', (idDraft, 'bozza'))
            db.commit()
            return True
        except Exception as e:
            log_error(f'{e}')
            return False

def find_stats():
    with sqlite3.connect(DB) as db:
        try:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            sql= """  SELECT SUM(CASE WHEN firstDay = 'friday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN secondDay = 'friday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN thirdDay = 'friday' THEN 1 ELSE 0 END) AS statFriday,

                SUM(CASE WHEN firstDay = 'saturday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN secondDay = 'saturday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN thirdDay = 'saturday' THEN 1 ELSE 0 END) AS statSaturday,

                SUM(CASE WHEN firstDay = 'sunday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN secondDay = 'sunday' THEN 1 ELSE 0 END) +
                SUM(CASE WHEN thirdDay = 'sunday' THEN 1 ELSE 0 END) AS statSunday
            FROM tickets;"""

            cursor.execute(sql)
            r_elements = cursor.fetchone()
            if not r_elements:
                return(False, f'no elements')

            elements = dict(r_elements)
            return(True, elements)
        except Exception as e:
            log_error(f'{e}')
            return(False, f'{e}')


            