(function() {


    let button_filter = document.querySelector('.button_filter')
    let filter_select = document.querySelector('.filter_select')
    
    function change_list () {
        if (filter_select.value != "Выберите страну") {
            button_filter.disabled = false
        } 
        else {
            button_filter.disabled = true
        }
    }
    if (filter_select) {
        filter_select.addEventListener('change', change_list)
    }


    let title_card = document.querySelector('.special__title_card')
    let season_list = document.querySelector('.special_list')

     function season_open () {
        let param = season_list.style.display
        console.log(param)
        if (param === "none") {
            season_list.style.display = "flex"
        }
        else {
            season_list.style.display = "none"
        }
    } 
    if (title_card) {
        title_card.addEventListener('click', season_open)
    }


    let title_card_2 = document.querySelector('.special__title_card-2')
    let preview_list = document.querySelector('.special_list-2')

    function preview_open () {
        let param = preview_list.style.display
        console.log(param)
        if (param === "none") {
            preview_list.style.display = "flex"
            console.log(param)
        }
        else {
            preview_list.style.display = "none"
            console.log(param)
        }
    } 
    if (title_card_2) {
        title_card_2.addEventListener('click', preview_open)
    }


    document.addEventListener('DOMContentLoaded', function() {
        let links = document.getElementsByClassName('all')
        for (let link of links) {
            link.href = "https://www.kinopoisk.ru/" + link.href.slice(22)
            link.target = "_blank"
          }
    })
})()

