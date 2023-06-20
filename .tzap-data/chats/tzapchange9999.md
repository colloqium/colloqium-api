

---
@role:assistant
Sure, instead of redirecting to the confirmation page, you can use JavaScript to display a pop-up dialog box asking the user to confirm the message. Here's an example of how you could use Bootstrap's Modal component to display a modal:

1. Remove the `redirect()` call and generate the system prompt.
2. Add the system prompt to the conversation.
3. Render the Interaction template, passing in the form and the conversation.
4. In the template, add a button that will trigger the display of the modal.
5. Add the modal HTML to the template, and use JavaScript to fill in the modal with the system message and recipient data.
6. Add an event listener to the "Send" button in the modal to trigger a POST request to the confirmation route.

Here's how you could modify the `interaction()` function to accomplish this:

```python
# ...

from flask import render_template

# ...

@interaction_bp.route("/", methods=['GET', 'POST'])
def interaction():

    form = InteractionForm()

    if form.validate_on_submit():
        # ...

        # Generate the new interaction's system prompt and add it to the conversation
        system_prompt = get_campaign_text_message_system_prompt(new_interaction)
        conversation = add_message_to_conversation(conversation, system_prompt)
        new_interaction.conversation = conversation
        db.session.commit()

        # Render the Interaction template, passing in the form and conversation
        return render_template('interaction.html',
                               form=form,
                               conversation=conversation)

    # ...
```

In your `templates/interaction.html` file, add something like the following at the bottom of the page:

```html
<!-- Button trigger modal -->
<button type="button" class="btn btn-primary" data-toggle="modal" data-target="#confirmationModal">
    Send message
</button>

<!-- Modal -->
<div class="modal fade" id="confirmationModal" tabindex="-1" role="dialog" aria-labelledby="confirmationModalLabel"
     aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="confirmationModalLabel">Confirm message</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <p><span id="recipientName"></span>, are you sure you want to send this message:</p>
                <p id="systemMessage"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" id="sendButton" class="btn btn-primary">Send</button>
            </div>
        </div>
    </div>
</div>

<script>
    $(document).ready(function () {
        // When the modal is opened, fill in the recipient name and system message
        $('#confirmationModal').on('show.bs.modal', function (event) {
            var button = $(event.relatedTarget) // Button that triggered the modal
            var recipientName = button.data('recipientname') // Extract recipient name from data-* attributes
            var systemMessage = button.data('systemmessage') // Extract system message from data-* attributes

            var modal = $(this)
            modal.find('#recipientName').text(recipientName)
            modal.find('#systemMessage').text(systemMessage)
        })

        // When the "Send" button in the modal is clicked, submit the Interaction form with the "confirmed" field set to true
        $('#sendButton').click(function () {
            $('#confirmed').val('true')
            $('form').submit()
        })
    })
</script>
```

In the `modal-body` section, replace the placeholders with the appropriate Jinja2 template variables. Note that you will also need to include the Bootstrap and jQuery files in your `base.html` file.

With this modification, the user will see a dialogue box with the system message and recipient name, and can choose whether to send the message or not. If the user clicks "Send", the `confirm_message()` route will be called with the appropriate data, and the message will be sent.
---
@role:user
I feel like rather than redirecting I want to show a pop up with the message and have the user click yes or no
---
@role:assistant
Great! To trigger the confirmation page after the user submits the Interaction form, you will need to modify the `interaction()` route in your `routes.py` file. Here's one way to do that:

1. After the form is validated and all the data is processed, instantiate a new `Interaction` object.
2. Fill out the fields of the new `Interaction` object based on the form data.
3. Add the first message to the conversation and update the `Interaction` object.
4. Generate the system prompt and assign it to the `conversation` field of the `Interaction` object.
5. Redirect the user to the confirmation page, passing in the system prompt and the ID of the new `Interaction` object.
6. In the `confirm_message()` route, handle the POST request to actually send the message.

Here's what the modified `interaction()` function might look like:

```python
# ...

from flask import redirect, url_for

# ...

@interaction_bp.route("/", methods=['GET', 'POST'])
def interaction():

    form = InteractionForm()

    if form.validate_on_submit():

        # Instantiate a new Interaction object
        new_interaction = Interaction()

        # Fill out the fields of the new Interaction object
        # ...

        # Generate the first message and add it to the conversation
        initial_message = "Hello, how can I assist you today?"
        conversation = initialize_conversation(initial_message)
        initial_system_message = get_campaign_text_message_system_prompt(new_interaction)
        system_prompt = initial_system_message
        conversation = add_message_to_conversation(conversation, initial_system_message)
        new_interaction.conversation = conversation

        # Generate the new interaction's system prompt and assign it to the "conversation" field
        system_prompt = get_campaign_text_message_system_prompt(new_interaction)
        new_interaction.conversation = add_message_to_conversation(
            new_interaction.conversation, system_prompt)

        # Add the new interaction object to the database
        db.session.add(new_interaction)
        db.session.commit()

        # Redirect to the confirmation page, passing in the system prompt and the Interaction ID
        return redirect(url_for('confirm_message.confirm_message',
                                interaction_id=new_interaction.id,
                                system_prompt=system_prompt))

    # ...
```

Note that you will also need to import `redirect`, `url_for`, and `get_campaign_text_message_system_prompt` at the top of your `routes.py` file. Once you've made these changes, submitting the Interaction form should take the user to the confirmation page.
---
@role:user
I've added confirm_message.py and the confirm_message.html. How do I trigger this confirmation on the Interaction page as I submit the form.
---
@role:assistant
Sure thing! One way to achieve that is to add a confirmation page that displays the message before sending it. Here is one way to do it:

1. Create a new route in `routes.py` file that takes the `interaction_id` and displays the last message in the conversation for that interaction.
2. In that route function, retrieve the interaction and the message from the database.
3. Render a new template that displays the message and enables the user to confirm or go back to edit the message.
4. In the confirmation page template, include two buttons that will be used to either confirm or edit the message.
5. Once the user confirms the message, redirect to the `text_message` route and send the message.

Here's the updated code for `routes.py`:

```python
@interaction_bp.route("/confirm_message/<interaction_id>", methods=['GET', 'POST'])
def confirm_message(interaction_id):
    interaction = Interaction.query.get(interaction_id)
    conversation = interaction.conversation
    system_prompt = conversation[-1]['content']
    recipient_phone_number = interaction.recipient.recipient_phone_number

    if request.method == 'POST':
        send_message_body = conversation[-1]['content']
        call_send_message_api(recipient_phone_number, send_message_body)
        print(f"Message sent: {send_message_body}")
        return redirect(url_for('interaction.success'))

    return render_template('confirm_message.html',
                           content=system_prompt,
                           interaction_id=interaction_id)
```

I've added a confirmation template (`confirm_message.html`) that takes two inputs: `content` which is the message to be confirmed, and `interaction_id`. Here's the code for that template:

```html
{% extends "base.html" %}

{% block content %}
  <h1>Confirm Message</h1>
  <p>Are you sure you want to send the following message?</p>
  <p>{{ content }}</p>

  <form method='POST'>
    <button type='submit' name='confirm' value='true'>Send</button>
    <button type='submit' name='edit' value='true'>Edit</button>
  </form>
{% endblock %}
```
---
@role:user
When a user submits, the interaction form, allow them to confirm the first message before it is sent
