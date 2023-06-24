function sendInteraction(button) {
    var interactionId = button.getAttribute("data-interaction-id");
    console.log("Interaction ID: " + interactionId);
    var interactionMethod = button.getAttribute("data-interaction-method");
    console.log("Interaction Method: " + interactionMethod);

    var url = window.location.origin + '/' + interactionMethod;
    console.log("Url is " + url);
  
    // Update interaction status
    fetch(url, { 
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
      },
      body: JSON.stringify({ interaction_status: "human_confirmed", interaction_id: interactionId})
    })
    .then(function(response) {
      
      if (response.status != 200) {
        button.innerText = "Error";
      } else {
        button.innerText = "Sent";
      }
      button.disabled = true;
    })
    .catch(function(error) {
      button.innerText = "Error";
      console.error("Error: " + error);
      button.disabled = true;
    });
  }