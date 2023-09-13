DELETE FROM public.audience_voter
	WHERE NOT audience_id = 1;

DELETE FROM public.audience
	WHERE NOT id = 1;