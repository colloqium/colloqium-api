-- Step 3: Identify Affected Rows in "campaign_audience" Table
SELECT * FROM campaign_audience WHERE campaign_id IN (
  SELECT id FROM campaign WHERE campaign_name NOT LIKE '%Volunteer Recruitment Team Testing%'
);

-- Step 3: Identify Affected Rows in "interaction" Table
SELECT * FROM interaction WHERE campaign_id IN (
  SELECT id FROM campaign WHERE campaign_name NOT LIKE '%Volunteer Recruitment Team Testing%'
);

-- Step 4a: Delete Corresponding Rows in "campaign_audience" Table
DELETE FROM campaign_audience WHERE campaign_id IN (
  SELECT id FROM campaign WHERE campaign_name NOT LIKE '%Volunteer Recruitment Team Testing%'
);

-- Step 4b: Delete Corresponding Rows in "interaction" Table
DELETE FROM interaction WHERE campaign_id IN (
  SELECT id FROM campaign WHERE campaign_name NOT LIKE '%Volunteer Recruitment Team Testing%'
);

-- Step 5: Re-run the DELETE Query for "campaign" Table
DELETE FROM campaign WHERE campaign_name NOT LIKE '%Volunteer Recruitment Team Testing%';

DELETE FROM public.audience_voter
	WHERE NOT audience_id = 1;

DELETE FROM public.audience
	WHERE NOT id = 1;
	
-- Delete interactions that reference agents to be deleted
DELETE FROM interaction WHERE agent_id IN (SELECT id FROM agent);
	
DELETE FROM public.agent