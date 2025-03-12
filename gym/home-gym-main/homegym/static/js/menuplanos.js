function loadPlans() {
    fetch('/planos') 
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => { 
                    console.log(data);
                    // Process the data and update the HTML content
                    var container = $('#content');
                    container.empty();

                    plans = data[0];
                    order = data[1];

                    
                    var html='<div class="menu"> '
                    for (var planId in plans) {
                        var planDetails = plans[planId];
                        var planOrder = order[planId];

                        html += '<div class="containers plan' + planId + '"> <div class="content"> <img src=' + planDetails[4] + ' class="meusplanosimg" > <div class="text-overlay"> <h3>'+ planDetails[0]+'</h3> <p> Plano '+ planOrder +' </p></div> </div> </div>'
                        
                        console.log(planDetails[4]);
                    }
                    html += '</div>'
                    container.append(html);
                    container.removeClass('loaded').addClass('loaded');
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                });
            }

function PlanIdOrder(planNumber){ // returns planid using order
    fetch('/planosOrder')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {

            return data[planNumber];
            
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
}   




function checkIfPlanExists(PlanN){
    return fetch('/planosOrder')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            return data[PlanN] != undefined;
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return false;
        });
}
       
