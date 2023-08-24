import requests
import json

# ## Base URL
# base_url = "https://thawing-sierra-51587.herokuapp.com/"
## Senders
senders_data = [
    {
        "sender_name": "GOTV for All",
        "sender_information": "GOTV for all is a non partisan organization that is dedicated to getting out the vote for all people.",
        "phone_numbers": ["+17706924459"]
    },
    {
        "sender_name": "John Whitmire",
        "sender_information": "Strong leadership and commitment to public service defines John Whitmire. He has spent his adult life working for Houstonians in our states Capitol, and now, John is running for Houston Mayor. He wants to take his years of experience and put it to work to fight crime, stop corruption, and make Houston a better place to work and live. John has represented a large portion of Houston and Harris County in Austin focusing on improving public safety, economic development, and ensuring government works for the people - not special interests. As the Chair of the Senate Criminal Justice Committee, John has transformed Texas into a national leader in criminal justice reform by advocating his tough but smart crime positions. Whitmire's fight against crime has worked at the state level and now Houstonians are asking him to use his experience at the local level. John is known as a can do public servant. John often says Houston is not New York or Chicago – we are Houston. We can fix our problems. John is an active advocate for all our first responders, and John believes we must have the best fire and police departments in the country. Furthermore, John also advocates for small businesses in Houston and across Texas by championing policies that encourage economic growth. His deep understanding of how government works and his collaborative style of working across the aisle will allow him to transform City Hall, making it more efficient so that it benefits all Houstonians. Houston is a large metropolitan city and John believes we should continue to grow and respect our differences. Houston needs a leader who understands these distinctive qualities which allows us to celebrate our diversity. John Whitmire is the leader we need, and he needs your support in his run for the next Mayor of Houston. Let’s go to work!",
        "phone_numbers": ["+13468182973"]
    }
]

base_url = "https://colloqium.ngrok.dev/"
# senders_data = [
    
#     {
#             "sender_name": "GOTV for All",
#             "sender_information": "GOTV for all is a non partisan organization that is dedicated to getting out the vote for all people.",
#             "phone_numbers": ["+16174335929"]
#     },

#     {
#             "sender_name": "John Whitmire",
#             "sender_information": "Strong leadership and commitment to public service defines John Whitmire. He has spent his adult life working for Houstonians in our states Capitol, and now, John is running for Houston Mayor. He wants to take his years of experience and put it to work to fight crime, stop corruption, and make Houston a better place to work and live. John has represented a large portion of Houston and Harris County in Austin focusing on improving public safety, economic development, and ensuring government works for the people - not special interests. As the Chair of the Senate Criminal Justice Committee, John has transformed Texas into a national leader in criminal justice reform by advocating his tough but smart crime positions. Whitmire's fight against crime has worked at the state level and now Houstonians are asking him to use his experience at the local level. John is known as a can do public servant. John often says Houston is not New York or Chicago – we are Houston. We can fix our problems. John is an active advocate for all our first responders, and John believes we must have the best fire and police departments in the country. Furthermore, John also advocates for small businesses in Houston and across Texas by championing policies that encourage economic growth. His deep understanding of how government works and his collaborative style of working across the aisle will allow him to transform City Hall, making it more efficient so that it benefits all Houstonians. Houston is a large metropolitan city and John believes we should continue to grow and respect our differences. Houston needs a leader who understands these distinctive qualities which allows us to celebrate our diversity. John Whitmire is the leader we need, and he needs your support in his run for the next Mayor of Houston. Let’s go to work!",
#             "phone_numbers": ["+13468182973"]
#     }
# ]



# voters
voters_data = [
    # {
    #     "voter_name": "Adrian Obleton",
    #     "voter_profile": {
    #         "interests": "Adrian is a tech enthusiast who is interested in the latest gadgets and technology. He is also interested in politics and is a registered Democrat.",
    #         "policy_preferences": "Adrian is a strong supporter of the Green New Deal and is interested in learning more about how to get involved in the climate movement.",
    #         "prefered_contact_method": "Adrian prefers to be contacted by text message.",
    #     },
    #     "voter_phone_number": "(706)664-1258"
    # },
    # {
    #     "voter_name": "Harshita Rathore",
    #     "voter_profile": {
    #         "interests": "Harshita is a recent US immigrant who just got her Green Card",
    #     },
    #     "voter_phone_number": "5618895021"
    # }
]

# Audiences
audiences_data = [
    # {
    #     "audience_name": "Test Audience for sender 1",
    #     "sender_id": 1,
    #     "voters": [1],
    #     "audience_information": "This is a test audience"
    # },

    # {
    #         "audience_name": "Test Audience 2 for sender 1",
    #         "sender_id": 1,
    #         "voters": [2],
    #         "audience_information": "This is a second test audience"
    # },

    # {
    #         "audience_name": "Test Audience for sender 2",
    #         "sender_id": 2,
    #         "voters": [1],
    #         "audience_information": "This is a test audience"
    # },

    # {
    #         "audience_name": "Test Audience 2 for sender 2",
    #         "sender_id": 2,
    #         "voters": [2],
    #         "audience_information": "This is a second test audience"
    # }
]

# Campaigns
campaigns_data = [
	# {
	# 	"campaign_name": "GOTV for All",
	# 	"campaign_prompt": "Your goal is to get the voter to register to vote. If you don't already know find out what state they are in so that you can share the correct registration site with them. Be brief and friendly in your communications. Mirror back their texting style and try to build rapport.",
	# 	"sender_id": 1,
	# 	"campaign_goal": "Get the voter to register to vote",
	# 	"campaign_fallback": "Refer the voter to the campaign website, gotv.com",
	# 	"campaign_end_date": "2023-11-07",
	# },
	{
		"sender_id": 2,
		"campaign_name": "Volunteer Recruitment Team Testing",
		"campaign_prompt": "Your name is Sarah. You are a volunteer for John Whitmire's Mayoral race. You are reaching out to people who have supported John when he was in the State Senate. Your job is to get them to agree to volunteer and fill out the registration link. If they do agree, send them this link to register: mobilize.us/johnwhitmire/ Do not send the link unless they agree to volunteer. Be concise and friendly. Communicate how someone from their community or geography would be likely to speak.",
		"campaign_goal": "Get the voter to agree to volunteer for the campaign",
		"campaign_fallback": "Refer the voter to the campaign website, johnwhitmire.com",
		"example_interactions": "[ {  Trigger: Result: Wrong Number,  Body: Sorry about that! Thanks for letting me know, I'll mark that now.,  Data Item: Result: Wrong Number }, {  Trigger: Result: Moved,  Body: No worries, you can still get involved even if you aren't in Houston. Join us for a virtual phone bank by signing up here: mobilize.us/johnwhitmire/,  Data Item: Result: Moved }, {  Trigger: Support: Strong Whitmire,  Body: Fantastic, thank you so much for your support! We're thrilled to have you on the team. Can we count on you to help our campaign by sending texts, making calls or knocking on doors?,  Data Item: 1 - Strong Support }, {  Trigger: Support: Lean Whitmire ,  Body: Great! We're thrilled to have you on the team. We're committed to ampfying every voice in Houston, is there any issue that matters most to you?,  Data Item: 2 - Lean Support }, {  Trigger: Support: Undecided,  Body: Okay--thanks for letting me know! I'm volunteering for John because he is committed to being tough but smart on crime, ensuring our basic city services like garabage pick up are met, continuing to diversity Houston's economy and most importantly, bringing houston together. What issues matter most to you in the upcoming election? ,  Data Item: 3 - Undecided }, {  Trigger: Support: Lean Against,  Body: Okay--thanks for letting me know! I'm volunteering for John because he is committed to being tough but smart on crime, ensuring our basic city services like garabage pick up are met, continuing to diversity Houston's economy and most importantly, bringing houston together. What issues matter most to you in the upcoming election? ,  Data Item: 4 - Lean Against }, {  Trigger: Support: Strong Against,  Body: Okay! Thanks for sharing that with me. We're interested in connecting with people no matter who they're supporting. When you think about the upcoming election, what issues are on your mind?,  Data Item: 5 - Strong Against }, {  Trigger: Not Voting,  Body: Okay! Thanks for sharing that with me. We're expecting unprecedented voter turnout this November, may I ask what's keeping you from participating?,  Data Item: Not Voting }, {  Trigger: Needs to Register,  Body: No worries, you still have time to get registered before the November 7th election, Visit https://www.harrisvotes.com/Voter/Registration to print a voter registration application. You must be registered by October 10th to vote!,  Data Item:  }, {  Trigger: Volunteer: Send Texts,  Body: Great! To get signed up to send texts, just click here:https://www.mobilize.us/johnwhitmire/event/570510/,  Data Item: Volunteer: textbank }, {  Trigger: Volunteer: Make Calls,  Body: Great! To get signed up to make calls, just click here: https://www.mobilize.us/johnwhitmire/event/570468/,  Data Item: Volunteer: Phonebank }, {  Trigger: Volunteer: Never Send Texts,  Body: No worries! You can always find ways to get involved with us by checking out this link: https://www.mobilize.us/johnwhitmire/,  Data Item: Volunteer: Never Send Texts }, {  Trigger: Volunteer: Never Make Calls,  Body: No worries! You can always find ways to get involved with us by checking out this link: https://www.mobilize.us/johnwhitmire/,  Data Item: Volunteer: Never Make Calls }, {  Trigger: Volunteer: Later,  Body: Okay! I'll let the team know and we can ask you again at a later date, in the mean time stay up to date with our event by visiting mobilize.us/johnwhitmire/,  Data Item: Volunteer: Later }, {  Trigger: Wants to Donate,  Body: Thanks for your support! To make a donation, just visit https://secure.anedot.com/john-whitmire-campaign/main,  Data Item: Donor }, {  Trigger: Result: Deceased,  Body: I'm so sorry to hear that, our thoughts are with you and your family.,  Data Item: Result: deceased }, {  Trigger: Temporary Opt Out,  Body: I'll ask the team to temporarily remove you from receiving texts, have a great rest of your day!,  Data Item: Temp Opt Out }, {  Trigger: Nonsense,  Body: I’m a volunteer looking to talk with voters about upcoming Houston Mayoral election. I’d love to chat with you about the issues that you care about, but if you’re not interested, then have a good day!,  Data Item:  }, {  Trigger: Hostile,  Body: I'm sorry, my intention wasn't to start an argument or irritate you. I’m just a volunteer looking to talk with voters about the upcoming Houston Mayoral election because I believe there is real change that needs to be made in our city. I’d love to chat with you about the issues that you care about, but if you’re not interested, then have a good day.,  Data Item: Result: Hostile }, {  Trigger: Republican/Trump/MAGA,  Body: Okay! Thanks for sharing that with me. I’m just a fellow Houstonian who's volunteering for John Whitmire's campaign because I believe there is real change that needs to be made in our city, and we're looking to talk to voters no matter what party they're a member of. What issues are important to you in this cycle?,  Data Item:  }, {  Trigger: Invasion of Privacy,  Body: I'm sorry, my intention wasn't to start an argument or irritate you. Believe it or not, most people prefer that we text them than knocking on their door or calling them! I’m just a fellow Houstonian who's volunteering for John Whitmire's campaign because I believe there is real change that needs to be made in our city. If you'd like to talk about moving Houston forward, I'd love to hear what issues are important to you?,  Data Item:  }, {  Trigger: Can't Participate due to Hatch Act/Gov Employee,  Body: Okay! Thanks for letting me know. Would you prefer I take you off of our list?,  Data Item:  }, {  Trigger: I'm under 18,  Body: Okay! Folks of all ages can volunteer with our campaign and make a difference, but I'm happy to remove you from our list if you'd like.,  Data Item:  }, {  Trigger: I'm Driving,  Body: Thanks for being a safe driver! Reply here when you get a chance, I'd love to chat.,  Data Item:  }, {  Trigger: Who is John?,  Body: John Whitmire has served Houston and Harris County for 50 years in the Texas Legislature. He is the son of a social worker, and teacher. From an early age was taught the importance of giving back to the community. He worked at the local welfare office to pay his way through the University of Houston, it was there were he saw first hand how good government could positively impact people's lives. He decided to dedicate his life to lifting up Houstonians. Fastforward 50 years, John is now the Dean of the Senate and the Chair of the Criminal Justice Committee. He has prepared his whole life to be Mayor of Houston. We hope you can take a moment to help our campaign! Just visit johnwhitmire.com to join us!,  Data Item:  }, {  Trigger: Why is John Running?,  Body: John Whitmire is running for Mayor because he genuinely cares about Houston and its citizens, prioritizing their safety and well-being. With his experience and commitment to public service, he aims to make Houston an even better city. He believes in the power of unity and wants to make a positive difference in the lives of all Houstonians. We hope you can take a moment to help our campaign! Just visit johnwhitmire.com to jon us!,  Data Item:  }, {  Trigger: Opponents?,  Body: Several candidates have filed to run but we believe John is the only candidate with the necessary experience and vision to bring Houston together. We hope you can take a moment to help our campaign! Just visit mobilize.us/johnwhitmire/ to get started.,  Data Item:  }, {  Trigger: How did you get this number?,  Body: Sorry about that! We're texting from the public voter file, a database that anybody can access. I know it can be a bit strange to receive a text from a stranger, but most people prefer it to us knocking on their door! When you think about the upcoming Houston Mayoral election, what issues are on your mind?,  Data Item:  }, {  Trigger: Concerns Relating to John work in the TX Senate,  Body: Thanks for letting me know! You can contact his capital senate office at john.whitmire@senate.texas.gov, 512-463-0115,  Data Item:  }, {  Trigger: Attempts to Call You,  Body: Sorry I couldn't connect with you on the phone. Are there any questions I can answer here via text? You can also connect with the campaign by emailing info@johnwhitmire.com,  Data Item:  }, {  Trigger: Random Issue,  Body: I’m not sure about that issue, but I do know John's running to ensure public safety by being tough but smart on crime, to strengthen Houston's diverse economy and to bring his experience of being on the frontline of battle for equality to bring Houston together. You can learn more about where she stands on the issues here: https://johnwhitmire.com/issues,  Data Item:  }, {  Trigger: Issue: Reproductive Rights,  Body: While the Mayor has limitations on what can be done to ensure the bodily automony of a women's right to choose, John Whitmire has been on the frontline of fighting for Abortion access in Texas. ,  Data Item: Issue: Reproductive Rights }, {  Trigger: Issue: Economy,  Body: John Whitmire believes that Houston is a place of endless opportunity. We are the home of multi-billion dollar companys ranging from oil and gas to tech to medicine. John wants to ensure Houston maintains it's status as the Energy Capital of the World by working with the growing renewable energy sector. John is committed to supporting with small businesses across the city by making it easier to open a business, build a faciitly and connect to Houston's infrastucture. Most importantly, John will work with our local schools and universities to produce homegrown talent.,  Data Item: Issue: Economy }, {  Trigger: Issue: HISD Takeover,  Body: John disagrees with the takeover of HISD, in fact alongside collegeues from the Senate John filed SB 1662 which would have given TEA options other than a takeover with a new board of managers. However, now that the takeover is well underway, John believes it is important that we give TEA the benefit of the doubt and allow them to do the work they believe is necessary to help underpreforming schools. ,  Data Item: Issue: Education }, {  Trigger: Issue: Education,  Body: John believes that educatuon is the most important tool to folks out of poverty, prevent addiction and crime. He continuely voted against a school voucher system, against strigent oversight from the state, against banning diversity, equality and inclusion.,  Data Item: issue: education }, {  Trigger: Issue: Climate Change,  Body: John Whitmire strongly believes that climate change is real and affecting the daily lives of people in Houston. When the Big Freeze happened in 2021, he made it a top priority to investigate why the power grid failed, and if Houstonians could face more devasting climate disasters.,  Data Item: Issue: Climate Change }, {  Trigger: Issue: Guns,  Body: John Whitmire knows what it means to be a victim of gun violence. In 199?, while returning home from an evening with family, John & his wife and daughter were robbed at gun point. That moment has stayed with John. After the tradegy that unfolded in Uvalde, John put forth a red flag bill that was designed to allow courts to restrict gun ownership to those whose family has expressed concerns over their mental health. ,  Data Item: Issue: Guns }, {  Trigger: Issue: Healthcare,  Body: ?,  Data Item: Issue: Healthcare }, {  Trigger: Issue: Immigration,  Body: ?,  Data Item: Issue: Immigration }, {  Trigger: Issue: Child Care,  Body: ?,  Data Item: Issue: Child Care }, {  Trigger: Issue: LGBT Equality,  Body: John Whitmire has been a decades long, fierce champion of the LGBTQ+ community and has earned their endorsements for his campaigns throughout his public service career. He has fought to repel Texas' anti-gay bill for decades. ,  Data Item: Issue: LGBT Equality }, {  Trigger: Issue: Criminal Justice Reform,  Body: John is committed to working with community leaders, activitsts and police officers. He wants to bring them together to to ensure the safety of all Houstonians while reforming our criminal justice system to make it fairer and increasing its focus on rehabilitation. ,  Data Item: Issue: Criminal Justice Reform }, {  Trigger: Issue: Labor,  Body: John Whitmire is proudly endorsed by several labor unions, including the Texas Gulf Coast AFL-CIO, Houston Police Officer's Union and many others.,  Data Item: Issue: Labor }, {  Trigger: Issue: Crime,  Body: John knows what it means to be a victim of a crime. After he and his family were robbed at gunpoint in the garage, John made it a priority to ensure the safety of all Houstonians. As the chair of the Senate Criminal Justice Comittee, John has proven to be tough but smart on crime. ,  Data Item: Issue: Crime }]",
		"campaign_end_date": "2023-11-07"
	}
]

def send_post_request(url, data):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Response text: {response.text}")
    return response.status_code, response.json()

def post_senders():
    url = base_url + 'sender'
    for sender in senders_data:
        status_code, response_data = send_post_request(url, sender)
        print(f"Sender POST status code: {status_code}, data: {response_data}")

def post_voters():
    url = base_url + 'voter'
    for voter in voters_data:
        print(f"Posting voter: {voter}")
        status_code, response_data = send_post_request(url, voter)
        print(f"voter POST status code: {status_code}, data: {response_data}")

def post_audiences():
    url = base_url + 'audience'
    for audience in audiences_data:
        status_code, response_data = send_post_request(url, audience)
        print(f"Audience POST status code: {status_code}, data: {response_data}")

def post_campaigns():
    url = base_url + 'campaign'
    for campaign in campaigns_data:
        status_code, response_data = send_post_request(url, campaign)
        print(f"Campaign POST status code: {status_code}, data: {response_data}")

# Run these functions to start posting data
post_senders()
post_voters()
post_audiences()
post_campaigns()