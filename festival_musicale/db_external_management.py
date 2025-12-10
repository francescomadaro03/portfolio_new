import db_management as d
import random as r
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

RANDOM = r.randint(0,800)
RANDOM2 = r.randint(0,800)

def check_allowed_ticket(email):
    with sqlite3.connect('database_tester.db') as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            try:
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                element = cursor.fetchone()
                
                cursor.execute('SELECT mail FROM tickets WHERE mail = ?', (email,))
                allowed = cursor.fetchone()
                if allowed is None:
                    return True
                else:
                    return False
            except Exception as e:

                return False



def check_day(day):
    with sqlite3.connect('database_tester.db') as db:
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

           return False

def insert_ticket_into_db(email, ticketType, days):
    with sqlite3.connect('database_tester.db') as db:
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
            return False

def delete_all():
    with sqlite3.connect('database.db') as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute('DELETE FROM users WHERE email = ?', ('francesco.madaro03@gmail.com',))
        element = cursor.fetchall()
        d = dict(element)
        return d

def check_count_tickets_day():


    for i in range(800):
        email = f'prova{i}@gmail.com'
        days = ['friday', 'saturday', 'sunday']
        typeUser = ['organizzatore', 'partecipante']
        uType = typeUser[r.randint(0,1)]
        day = days[r.randint(0,2)]
        if i == RANDOM or i == RANDOM2:
            email = 'prova0@gmail.com'
        if check_allowed_ticket(email) and check_day(day):
            insert_ticket_into_db(email,'Single-day Ticket', [day]) 
        else:
            print('mail duplicata')
    
    with sqlite3.connect('database_tester.db') as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE firstDay = ?', ('friday',))
        element = cursor.fetchone()
        d = dict(element)
        return d



def insert_p():
    
    # SATURDAY
    performances = [ 
    [
        "11:00",
        "Melody Gardot",
        "B",
        75,
        "Jazz / Blues",
        ("Known for her sensual voice and sophisticated jazz arrangements, Melody Gardot crafts evocative live performances. "
         "Blending blues and jazz, her music radiates intimacy and cinematic mood, transporting listeners into deeply personal emotional landscapes."),
        "images/uploads/ml.jpeg",
        "framadaro2003"
    ],
    [
        "14:00",
        "Leon Bridges",
        "A",
        90,
        "Soul / R&B",
        ("With a warm, soulful voice reminiscent of classic R&B, Leon Bridges evokes the sounds of a bygone era. "
         "His vintage-inspired songs and smooth delivery create heartfelt, nostalgic performances that resonate across generations."),
        "images/uploads/lb.jpeg",
        "framadaro2003"
    ],
    [
        "16:00",
        "Rosalía",
        "C",
        60,
        "Flamenco / Pop",
        ("Modern icon Rosalía fuses traditional flamenco with contemporary pop and urban sounds. "
         "Her innovative style and bold artistry bring passion and drama to the stage, captivating audiences with a fresh take on cultural heritage."),
        "images/uploads/r.jpeg",
        "framadaro2003"
    ],
    [
        "18:00",
        "Marcus Miller",
        "A",
        90,
        "Jazz / Funk",
        ("Legendary bassist and composer Marcus Miller delivers powerful performances that combine jazz, funk, and soul. "
         "Known for his irresistible grooves and virtuosic playing, Miller’s shows are a celebration of rhythmic energy and musical mastery."),
        "images/uploads/mm.jpeg",
        "framadaro2003"
    ],
    [
        "20:00",
        "St. Vincent",
        "C",
        75,
        "Indie Rock / Art Pop",
        ("Innovative guitarist and singer St. Vincent crafts artful performances that blend indie rock with experimental pop. "
         "Her unique sound, theatrical stage presence, and inventive songwriting make her live shows compelling and boundary-pushing."),
        "images/uploads/sv.jpg",
        "framadaro2003"
    ]
    ]


    with sqlite3.connect('database.db') as db:
        cursor = db.cursor()
        sql = """
            INSERT INTO performances
            (artist, day, start, duration, stage, genre, image, description, typePost, creator)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Supponiamo che le prime 5 siano sabato
        for perf in performances:
            artist = perf[1]
            day = 'sunday'
            start = perf[0]
            duration = perf[3]
            stage = perf[2]
            genre = perf[4]
            description = perf[5]
            image = perf[6]
            typePost = 'pubblicato'
            creator = perf[7]

            cursor.execute(sql, (artist, day, start, duration, stage, genre, image, description, typePost, creator))
        db.commit()



delete_all()
