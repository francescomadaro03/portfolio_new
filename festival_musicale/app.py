from flask import Flask, render_template, url_for, request, redirect, jsonify
import re
from db_management import check_both_username_email, insert_user_in_db, retrieve_user, check_day, check_allowed_ticket, insert_ticket_into_db, check_free_spot, insert_performance_into_db, retrieve_editable_performances, retrieve_ticket_info, retrieve_performance, edit_performance, check_artist_integrity, all_performances, delete_draft, find_stats
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from user import User
import os
from urllib.parse import urlparse, urljoin


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https') and
        ref_url.netloc == test_url.netloc
    )

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config["SECRET_KEY"] = 'PPCQsVnhKdYJDKoPb4bYLlDD'
UPLOADS_FOLDER = 'static/images/uploads'
app.config["UPLOAD_FOLDER"] = UPLOADS_FOLDER

@login_manager.user_loader
def load_user(id):
    profile = retrieve_user(id)
    user = User(profile["name"], profile["surname"], profile["email"], profile["username"], profile["type"])
    return user

@app.route('/')
def home():
    performances_list = all_performances(True)
    if performances_list[0] == True:
        performances = performances_list[1]
        return render_template('home.html', perf=performances)
    else:
        app.logger.warning(performances_list[1])
        return(render_template('home.html', error=f'no performances'))

@app.route('/signin')
def sign_in():
    w_mail = request.args.get('w_mail') == 'True'
    w_password = request.args.get('w_password') == 'True'
    w_username = request.args.get('w_username') == 'True'
    w_confirm = request.args.get('w_confirm') == 'True'
    return render_template('signIn.html', w_mail = w_mail, w_password = w_password, w_username = w_username, w_confirm = w_confirm)

@app.route('/newUser', methods=["POST"])
def new_user():
    name = request.form.get('name')
    surname = request.form.get('surname')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')
    if password != confirm_password:
        return redirect(url_for('sign_in', w_confirm = True))

    user_type = request.form.get('type')

    password_pattern = r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}"
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    secure_password = bool(re.match(password_pattern, password))
    secure_mail = bool(re.match(email_pattern, email))




    if secure_mail is False:
        return redirect(url_for('sign_in', w_mail = True))
    if secure_password is False:
        return redirect(url_for('sign_in', w_password = True))

    check_integrity = check_both_username_email(email, username)

    if check_integrity == 'ok' and secure_mail is True and secure_password is True:
        password_hash = generate_password_hash(password)
        if insert_user_in_db(name, surname, email, password_hash, username, user_type):
            return redirect(url_for('ok'))
        else:
            return redirect(url_for('error'))
    elif check_integrity == 'mail already in db':
        return redirect(url_for('sign_in', w_mail = True ))
    elif check_integrity == 'username already in db':
        return redirect(url_for('sign_in', w_username = True))
    else:
        return redirect(url_for('error'))

@app.route('/confirmNewUser') 
def ok():
    return render_template('ok.html')

@app.route('/login')
def login():
    w_user = request.args.get('w_user') == 'True'
    w_pw = request.args.get('w_pw') == 'True'
    nextUrl = request.args.get('next')

    return render_template('login.html', w_user = w_user, w_pw = w_pw, target=nextUrl)

@app.route('/auth/<string:target>', methods=["POST"])
def auth(target):
    identifier = request.form.get('username-mail')
    password = request.form.get('password')

    
    profile = retrieve_user(identifier)
    if profile is None:
        return redirect(url_for('login', w_user = True))

    check_pw = bool(check_password_hash(profile["password"], password))
    if not check_pw:
        return redirect(url_for('login', w_pw = True))
    else:
        user = load_user(profile["email"])
        login_user(user)
        app.logger.warning(f'{target}')
        if target != 'None' and is_safe_url(target):
            return redirect(url_for(target))
        else:
            return redirect(url_for('home'))
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/tickets')
@login_required
def tickets():
    return render_template('tickets.html')

@app.route('/checkout')
@login_required
def checkout():
    ticket_type = request.args.get('t')
    w_payment = request.args.get('w_payment') == 'True'
    w_personal = request.args.get('w_personal') == 'True'
    invalid_day = request.args.get('invalid_day') == 'True'

    if ticket_type == 'singleDay':
        tt = 'Single-day Pass'
    elif ticket_type == 'twoDay':
        tt = 'Two-day Pass'
    else:
        tt = 'Full Pass'

    if current_user.type == 'organizzatore':
        return redirect(url_for('error'))

    return render_template('checkout.html', tt=tt, w_payment = w_payment, w_personal=w_personal, invalid_day = invalid_day)

@app.route('/buyTicket', methods=["POST"])
@login_required
def buy_ticket():
    email = request.form.get('email')
    ticket_type = request.form.get('ticketType')
    if ticket_type == 'Single-day Pass':
        tt = 'singleDay'
    elif ticket_type == 'Two-day Pass':
        tt = 'twoDay'
    else:
        tt = 'fullPass'
    day_string = request.form.get('day')
    day_list = day_string.split('-')

    nome = request.form.get('name')
    cognome = request.form.get('surname')
    city = request.form.get('city')
    cap = request.form.get('cap')
    prov = request.form.get('prov')
    cc_name = request.form.get('cc-name')
    cc_number = request.form.get('cc-number')
    expiration_date = request.form.get('expiration-date')
    cc_cvv = request.form.get('cc-cvv')

    if (
        len(nome) > 40 or len(cognome) > 40 or len(city) > 40 or
        len(nome) < 3 or len(cognome) < 3 or len(city) < 3 or
        not re.fullmatch(r"\d{5}", cap) or
        not re.fullmatch(r"[A-Za-z]{2}", prov)
    ):
        return redirect(url_for('checkout', w_personal=True, tt=tt))
    
    ticket_format = {'Full Pass', 'Single-day Pass', 'Two-day Pass'}
    if ticket_type not in ticket_format:
        return redirect(url_for('error', error='day not featured in festival'))

    
    if len(cc_name) < 10 \
    or not re.fullmatch(r"(?:\d{4} ?){4}", cc_number) \
    or not re.fullmatch(r"(0[1-9]|1[0-2])/[0-9]{2}", expiration_date) \
    or not re.fullmatch(r"\d{3}", cc_cvv):
        
        return redirect(url_for('checkout', w_payment=True, t=tt))




    for i in range(len(day_list)):
        if day_list[i] not in {'friday', 'saturday', 'sunday'} :
            return (redirect(url_for('checkout', invalid_day = True, t=tt)))
        flag = check_day(day_list[i])
        if flag == False:
            return(redirect(url_for('checkout', full_day = True, t=tt)))
    
    is_user_allowed = check_allowed_ticket(email)


    if is_user_allowed == True:
        insert_ticket_into_db(email, ticket_type, day_list)
        return redirect(url_for('home'))
    
    return redirect(url_for('error', error='ticket already bought'))

@app.route('/error')
@login_required
def error():
    return render_template('error.html')

@app.route('/performance')
@login_required
def performance():
    # validazione accesso solo per gli organizzatori
    if current_user.type == 'partecipante':
        app.logger.warning('Il profilo non può accedere a questa route')
        return redirect(url_for('home'))

    invalid_data = request.args.get('invalid_data') == 'True'
    artist = request.args.get('artist') == 'True'
    day = request.args.get('day') == 'True'
    start = request.args.get('start') == 'True'
    duration = request.args.get('duration') == 'True'
    stage = request.args.get('stage') == 'True'
    genre = request.args.get('genre') == 'True'
    description = request.args.get('description') == 'True'






    #inseire check vietato ai partecipanti
    return render_template('performance.html', invalid_data=invalid_data, artist=artist, day=day, start=start, duration=duration, stage=stage, genre=genre, description=description)

@app.route('/addPerformance', methods=["POST"])
@login_required
def addPerformance():

    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg']

    artist = request.form.get('artist')#fatto
    day = request.form.get('day') #fatto
    start = request.form.get('start')#fatto
    duration = request.form.get('duration')#fatto
    stage = request.form.get('stage')#fatto
    genre = request.form.get('genre')
    image = request.files.get('file')  
    type_post = request.form.get('type_post')
    description = request.form.get('description')

    #401 for organizzatori

    if current_user.type == 'partecipante':
        app.logger.warning('Il profilo non può accedere a questa route')
        return redirect(url_for('home'))

    #validazione form 


    if not artist or not day or not start or not duration or not stage or not genre or not image or not type_post or not description:
        app.logger.warning("Form inviato con alcuni dati mancanti")
        return redirect(url_for('performance', invalid_data = True))
    
    if not re.match(r'^\d{2,3}$', duration):
        app.logger.warning('Errore nel formato della durata')
        return redirect(url_for('performance', invalid_data = True))
    else:
        dur_int = int(duration)
        if dur_int < 10 or dur_int > 121:
            app.logger.warning('Durata fuori range')
            return redirect(url_for('performance', invalid_data = True))

    
    if (day != 'friday' and day != 'saturday' and day != 'sunday'):
        app.logger.warning('Errore nella scelta dei giorni')
        return redirect(url_for('performance', invalid_data = True))
    
    if (stage != 'A' and stage != 'B' and stage != 'C'):
        app.logger.warning('Errore nello stage')
        return redirect(url_for('performance', invalid_data = True))

    
    if re.match(r'^[0-9]{2}:[0-9]{2}$', start):
        digits = start.split(':')
        if int(digits[0]) < 10 or int(digits[0]) > 23 or int(digits[1]) < 0 or int(digits[1]) >= 60:
            app.logger.warning('Errore nelle cifre orarie. orario non valido')
            return redirect(url_for('performance', invalid_data = True))
        
    else:
        app.logger.warning('Errore nel formato orario')
        return redirect(url_for('performance', invalid_data = True))

    if not re.match(r"^[A-Za-zÀ-ÿ0-9\s'&./,\-#]+$", artist): #ammette lettere maiuscile, minuscole, accentate, spazi, numeri, slash, virgole cancelletto e apostrofo
        app.logger.warning('Errore nel formato del nome degli artisti')
        return redirect(url_for('performance', invalid_data = True))

    image_name = image.filename
    
    if '.' in image_name:
        if not image_name.rsplit('.')[1].lower() in ALLOWED_EXTENSIONS:
            app.logger.warning('Estensione non valida')
            return redirect(url_for('performance', invalid_data = True))
    else:
        app.logger.warning('il file caricato non presenta estensioni')
        return redirect(url_for('performance', invalid_data = True))
    
    if type_post != 'bozza' and type_post != 'pubblicato':
        app.logger.warning('Errore nel tipo di richiesta inviata frontend')
        app.logger.warning(type_post)
        return redirect(url_for('performance', invalid_data = True))
    
    if not re.match(r"^[A-Za-zÀ-ÿ0-9\s'&./,\-#]+$", genre):
        app.logger.warning('Errore nel formato del genere musicale')
        return redirect(url_for('performance', invalid_data = True))
                
    if len(description) > 1000:
        app.logger.warning('Errore nel formato della descrizione')
        return redirect(url_for('performance', invalid_data = True))
                
    #controllo mancanza di sovrapposizioni (eseguito in db_management)

    check_spot = check_free_spot(stage,day,start,duration)
    check_artist = check_artist_integrity(artist)

    #controllo del posto ed eventuale push nel database


    if check_artist[0] == False:
        app.logger.warning(check_artist[1])
        return redirect(url_for('performance', invalid_data = True))
    elif check_spot[0] == False:
        app.logger.warning(f'Errore: {check_spot[1]}')
        return redirect(url_for('performance', invalid_data = True))
    else:
        #gestione del file
        sec_name = secure_filename(image_name)
        filepath = f'{UPLOADS_FOLDER}/{sec_name}'
        filepath_db = f'/images/uploads/{sec_name}'
        if insert_performance_into_db(artist, day, start, duration, stage, genre, filepath_db, description, type_post, current_user.username):
            image.save(filepath)
            return redirect(url_for('home'))
        else:
            return redirect(url_for('performance', not_in_db = True))
        

@app.route('/updatePerformance', methods=["POST"])
@login_required
def update_performance():
    if current_user.type == 'partecipante':
        app.logger.warning('utente non autorizzato per questa route')
        return redirect(url_for('home.html'))

    #validazione form
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg']



    artist = request.form.get('artist')#fatto
    day = request.form.get('day') #fatto
    start = request.form.get('start')#fatto
    duration = request.form.get('duration')#fatto
    stage = request.form.get('stage')#fatto
    genre = request.form.get('genre')
    image = request.files.get('file')  
    type_post = request.form.get('type_post')
    description = request.form.get('description')
    idPerformance = request.form.get('id')

    error = ""

    if len(artist) < 3 or len(artist) > 30:
        app.logger.warning("Dato artista non corretto")
        return redirect(url_for('error', error="Dato artista non corretto"))

    if day not in {'friday', 'saturday', 'sunday'}:
        app.logger.warning('Giornata non valida')
        return redirect(url_for('error', error='giornata non valida'))
    
    if re.match(r'^[0-9]{2}:[0-9]{2}$', start):
        digits = start.split(':')
        if int(digits[0]) < 0 or int(digits[0]) > 23 or int(digits[1]) < 0 or int(digits[1]) >= 60:
            app.logger.warning('Errore nelle cifre orarie')
            return redirect(url_for('error', error='errore nelle cifre'))
    else:
        app.logger.warning('errore nel formato orario')
        return redirect(url_for('error', error='errore nelle cifre orarie'))

    try: 
        durationNumber = int(duration)
        if durationNumber<10 or durationNumber > 120:
            app.logger.warning('Errore nel formato durata')
            return redirect(url_for('error', errore='errore nel formato data'))
    except Exception as e:
        app.logger.warning(f'{e}')
        return redirect(url_for('error', error=f'{e}'))
    
    if stage not in {'A', 'B', 'C'}:
        app.logger.warning('Errore nella selezione del palco')
        return redirect(url_for('error', error='Errore nella selezione del palco'))

    if len(description)<10 or len(description) > 1000:
        app.logger.warning('Errore nel formato descrizione')
        return redirect(url_for('error', errore='errore nel formato descrizione'))
    
    if len(genre)<3 or len(genre) > 20:
        app.logger.warning('Errore nel formato genere')
        return redirect(url_for('error', errore='errore nel formato genere'))

    if type_post not in {'pubblicato', 'bozza'}:
        app.logger.warning('Errore nel tipo di post')
        return redirect(url_for('error', error='Errore nel tipo di post'))

    #funzionamento
    image_new_url = None
    image_name = image.filename
    

    oldPerformance = retrieve_performance(idPerformance)[1]
    if image_name != '' and isinstance(oldPerformance, dict):
        app.logger.warning(f'{image_name.rstrip('.')[1]}')
        if not image_name.rsplit('.')[1].lower() in ALLOWED_EXTENSIONS:

            app.logger.warning('File non supportato')
            return redirect(url_for('error'))
        image_name_secure = secure_filename(image_name)
        image.save(f'static/images/uploads/{image_name_secure}')
        image_new_url = f'/images/uploads/{image_name_secure}'
        app.logger.warning(image_new_url)

    spot = check_free_spot(stage, day, start, duration, idPerformance)
    if spot[0] == False:
        app.logger.warning('No spots for this new concert')
        return redirect(url_for('error', error=spot[1]))
    
    check_artist = check_artist_integrity(artist, idPerformance)
    
    if check_artist[0] == False:
        app.logger.warning(f'{check_artist[1]}')
        return redirect(url_for('error', error=check_artist[1] ))

    flag = edit_performance(idPerformance, artist, day, start, duration, stage, genre, image_new_url, description, type_post)
    if flag[0] == True:
        app.logger.warning('Performance modificata correttamente')
        return redirect(url_for('profile'))
    else:
        app.logger.warning('Errore di aggiornamento della performance')
        return redirect(url_for('error'))

        
        






    
    




    

  
    

@app.route('/profile')
@login_required
def profile():
    if current_user.type == 'organizzatore':
        all_performances_list = all_performances(True)
        list_of_editable_performances = retrieve_editable_performances(current_user.username)
        if list_of_editable_performances[0] == False or all_performances_list[0] == False:
            app.logger.warning(f'{all_performances_list[0]}')
            return redirect(url_for('error'))
        else:
            if list_of_editable_performances[1] == 'no performances':
                return render_template('profile.html',type='organizzatore' , e_performances = 'No performances', a_performances = all_performances_list[1])
            else:
                return render_template('profile.html',type='organizzatore' , e_performances= list_of_editable_performances[1], a_performances = all_performances_list[1])
    else:
        ticket_info = retrieve_ticket_info(current_user.email)
        if(ticket_info[0] == False):
            app.logger.warning(f'{ticket_info[0]}')
        else:
            if ticket_info[1] == 'no tickets found':
                return render_template('profile.html', type='partecipante' , ticket_info= 'none')
            else:
                return render_template('profile.html', type='partecipante' , ticket_info=ticket_info[1])
        
@app.route('/getPerformance', methods=["POST"])
@login_required
def get_performance_for_edit():
    requestSent = request.get_json()
    idRequest = requestSent['id']
    performance = retrieve_performance(idRequest)
    if performance[0] == True:
        if performance[1] == 'no performance found':
            return jsonify({'error': 'no performance found'}), 404
        else:
            return jsonify(performance[1]), 200
    else:
        return jsonify({'error': 'database could not send performance'}), 500
    
@app.route('/details/<int:idPerformance>')
def details(idPerformance):
    detailsPerformance = retrieve_performance(idPerformance)
    if(detailsPerformance[0] == False):
        return redirect(url_for('error'))
    return render_template('performanceDetails.html', performance=detailsPerformance[1])

@app.route('/deleteDraft', methods=['DELETE'])
@login_required
def delete():
    answer = request.get_json()
    idDraft = answer['id']
    flag = delete_draft(idDraft)
    if flag == True:
        return jsonify({'status': 'ok'}), 200
    else:
        return jsonify({'error':'database could not delete draft'}), 500


@app.route('/ticketStats')
@login_required
def stats():
    statistics = find_stats()
    if statistics[0] == False:
        return jsonify({'error': 'database did not retrieve stats'}), 500
    else:
        return jsonify(statistics[1]), 200
