async function findPerformance(id) {
    console.log(id)
    try {
        const response = await fetch('/getPerformance',
        {
            method: "POST",
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'id': id})
        }

        )

        if (!response.ok){
            alert('Errore')
        }
        else {
            data = await response.json()
            console.log(data)
            setFrontEnd(data)
        }
    }
    catch (error) {
        console.log(error)
        alert('Qualcosa è andato storto')
    }
}

function setFrontEnd(data){
    
    document.getElementById('artist').value = data.artist
    document.getElementById('day').value = data.day
    document.getElementById('start').value= data.start
    document.getElementById('duration').value = data.duration
    document.getElementById('genre').value = data.genre
    document.getElementById('description').value = data.description

    console.log(data.id)

    document.getElementById('id').value = data.id
    const wrapper = document.getElementById('image')
    const img = document.createElement('img')
    img.classList.add('img')
    img.src = 'static' + data.image
    img.height = '470'
    img.width = '470'
    img.alt = 'artist image'
    wrapper.appendChild(img)

    document.getElementById('visualizza').href = 'static' + data.image




}

function triggerNewFile() {
    document.getElementById('image').style.display = 'none'
    document.getElementById('newFile').style.display = 'block'
    document.getElementById('file').required = true
}

const modal = document.getElementById('staticBackdrop')

    
function resetModal() {


    images = document.querySelectorAll('.img')
    images.forEach((i) => {
        i.remove()
    } )
}

async function deleteDraft(id){
    const response = await fetch('/deleteDraft',{
        method: 'DELETE',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({'id' : id})
    })

    if(!response.ok){
        window.location.href = '/error'
    }
    else{
        window.location.href = '/profile'
    }
}

async function statistics(){
    try {
        const response = await fetch('/ticketStats')
        if(!response.ok){
            throw new Error('Error from database')
        }
        else{
            const data = await response.json()
            return data
        }
    } catch (err) {
        console.log(err)
        window.location.href = '/error'
    }
}

function percentageOn200(number){
    return parseInt(number)/2
}


document.addEventListener('DOMContentLoaded', async function () {
    const data = await statistics()
    console.log(data)
    const fridayCount = data.statFriday
    const percFriday = percentageOn200(fridayCount)
    console.log(percFriday)
    const rectFriday = document.getElementById('fridayRect')
    rectFriday.setAttribute('height', percFriday + '')
    rectFriday.setAttribute('y', (100-percFriday) + '')


    const saturdayCount = data.statSaturday
    const percSaturday = percentageOn200(saturdayCount)
    console.log(percSaturday)
    const rectSaturday = document.getElementById('saturdayRect')
    rectSaturday.setAttribute('height', percSaturday + '')
    rectSaturday.setAttribute('y', (100-percSaturday) + '')
    
    const sundayCount = data.statSunday
    const percSunday = percentageOn200(sundayCount)
    console.log(percSunday)
    const rectSunday = document.getElementById('sundayRect')
    rectSunday.setAttribute('height', percSunday + '')
    rectSunday.setAttribute('y', (100-percSunday) + '')
    
})