# Contoso Telecom - Mobile Data and Signal Troubleshooting Guide

Document ID: KB-TS-010
Classification: Synthetic training content for the Microsoft Foundry agent lab.

Use this guide to choose first troubleshooting steps for mobile data, signal, and home internet issues.
Always check the Known Incidents Bulletin first.

## No signal (no bars, or a "no signal" icon such as a circle with a line through it)
1. Check the Known Incidents Bulletin for the customer's area.
2. Ask the customer to switch Airplane mode on for 10 seconds and then off.
3. Restart the phone.
4. Check that the SIM or eSIM is enabled in the phone settings.
5. If the customer recently moved home, the new address may be in an area with weaker indoor coverage.
   Raise a coverage check with Network Operations including the customer's new area name.

## No mobile data, but calls and SMS work
1. Check the Known Incidents Bulletin for the area.
2. Confirm that mobile data is switched on and that the customer has an active data bundle or balance.
3. Check the Access Point Name (APN) is set to `contoso.internet` (fictional value).
4. Restart the phone.

## Slow home internet in the evening
1. Evening slowdowns are often caused by Wi-Fi congestion inside the home.
2. Ask the customer to restart the router and test speed with a cable connection if possible.
3. If speeds are still below 50% of the plan speed on a cable connection, raise the issue with Network Operations at priority P3.

## Calls dropping
1. Check the Known Incidents Bulletin for the area.
2. Ask whether drops happen in one location or everywhere.
3. Suggest Wi-Fi Calling as a temporary workaround.
