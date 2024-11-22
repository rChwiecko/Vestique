# First import standard library modules
import logging
import sys
import os
import time
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Then import third-party modules
import streamlit as st
from PIL import Image
import numpy as np
from dotenv import load_dotenv
import json

# Finally import your local modules
from feature_extractor import FeatureExtractor
from wardrobe_tracker import WardrobeTracker
from wardrobe_notifier import EmailNotifier
from decider import decide_preference
from event_loop import background_loop
from email_settings import initialize_email_settings
from market_place_manager import Marketplace
from decide_match import decide_match

from dotenv import load_dotenv
from SambaFit import *
from style_advisor import StyleAdvisor
from preferences_tab import preferences_tab

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
SAMBANOVA_API_KEY = 'ba4070a0-299d-4e64-8952-0886808164b3'
best = [
{ "type": "blazer", "material": "polyester blend", "color": { "primary": "beige", "secondary": [] }, "fit_and_style": { "fit": "slightly relaxed", "style": "contemporary" }, "design_features": { "closure": "single-breasted with single button", "lapel": "notched", "sleeves": "long, cuffless" }, "condition": "new or like-new", "brand": "unknown", "season": "all-season", "use_case": ["professional settings", "casual outings"], "size": "unknown" }
]

worst = [
    { "type": "sweatshirt", "material": "cotton blend", "color": { "primary": "dark navy blue", "secondary": ["white graphic"] }, "fit_and_style": { "fit": "relaxed", "style": "casual" }, "design_features": { "collar": "hooded", "closures": ["drawstring"], "embellishments": ["graphic print"], "logo": "none" }, "condition": "new", "brand": "unknown", "season": "all-season", "use_case": ["travel", "casual outings"], "size": "unknown" }
]
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
def style_advisor_tab(tracker):
    # Add custom styling with proper padding and dark theme
    st.markdown("""
        <style>
            /* Container styling */
            .main-container {
                background-color: #1E1E1E;
                padding: 20px;
                border-radius: 12px;
                margin: 10px 0;
            }
            
            /* Image and content grid */
            .grid-container {
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 20px;
                margin: 20px 0;
            }
            
            /* Image card */
            .image-card {
                background-color: #2D2D2D;
                border-radius: 12px;
                padding: 16px;
                text-align: center;
            }
            
            /* Advice container */
            .advice-container {
                background-color: #2D2D2D;
                border-radius: 12px;
                padding: 24px;
                margin-top: 10px;
            }
            
            /* Typography */
            .item-title {
                color: #E0E0E0;
                font-size: 1.2rem;
                margin: 12px 0;
                text-align: center;
            }
            
            .advice-text {
                color: #CCCCCC;
                line-height: 1.6;
                font-size: 1rem;
            }
            
            /* Sources section */
            .sources {
                margin-top: 20px;
                padding-top: 16px;
                border-top: 1px solid #3D3D3D;
                color: #888888;
                font-size: 0.9rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.subheader("👔 Style Advisor")
    
    if 'style_advisor' not in st.session_state:
        st.session_state.style_advisor = StyleAdvisor(SAMBANOVA_API_KEY)
    
    if tracker.database["items"]:
        selected_item = st.selectbox(
            "Select an item for styling advice",
            options=tracker.database["items"],
            format_func=lambda x: x.get('name', x['type'])
        )
        
        if selected_item:
            try:
                # Debug output
                if st.session_state.get('debug_mode', False):
                    st.write("Selected item:", selected_item)
                
                # Get the AI analysis
                ai_analysis = selected_item.get('ai_analysis')
                if not ai_analysis:
                    st.warning("This item doesn't have AI analysis data.")
                    return

                # Parse the AI analysis and extract item type
                try:
                    if isinstance(ai_analysis, str) and '```json' in ai_analysis:
                        # Extract JSON between markdown code blocks
                        json_content = ai_analysis.split('```json\n')[1].split('\n```')[0]
                        ai_data = json.loads(json_content)
                    elif isinstance(ai_analysis, str):
                        # Use the raw string if no markdown
                        ai_data = json.loads(ai_analysis)
                    else:
                        # If it's already a dict, use it directly
                        ai_data = ai_analysis

                    # Use the more specific type from AI analysis if available
                    item_type = ai_data.get('type') or selected_item.get('type', 'Unknown')

                    # Combine with item metadata
                    item_description = {
                        'name': selected_item.get('name', 'Unknown'),
                        'type': item_type,  # Use the more specific type from AI analysis
                        'brand': selected_item.get('brand', ai_data.get('brand', 'Unknown')),
                        'color': ai_data.get('color', {}),
                        'fit_and_style': ai_data.get('fit_and_style', {}),
                        'material': ai_data.get('material', 'Unknown'),
                        'design_features': ai_data.get('design_features', {}),
                        'condition': ai_data.get('condition', 'Unknown'),
                        'season': ai_data.get('season', 'Unknown'),
                        'use_case': ai_data.get('use_case', [])
                    }

                    # Create display grid
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if 'image' in selected_item:
                            image = tracker.base64_to_image(selected_item['image'])
                            if image:
                                st.image(image, use_column_width=True)
                        
                        st.markdown(f"### Item Details")
                        st.markdown(f"**Type:** {item_type}")
                        st.markdown(f"**Material:** {item_description['material']}")
                        if 'design_features' in ai_data:
                            st.markdown("**Features:**")
                            for key, value in ai_data['design_features'].items():
                                if isinstance(value, list):
                                    st.markdown(f"- {key}: {', '.join(value)}")
                                else:
                                    st.markdown(f"- {key}: {value}")

                    with col2:
                        with st.spinner("Getting style advice..."):
                            # Get style advice using the enhanced item description
                            advice = st.session_state.style_advisor.get_style_advice(item_description)
                            
                            # Display advice
                            st.markdown("### Styling Tips")
                            st.markdown(advice["styling_tips"])
                            
                            # Display sources
                            with st.expander("Sources"):
                                for source in advice["sources"]:
                                    st.caption(f"- {source}")

                    

                except json.JSONDecodeError as e:
                    st.error(f"Error parsing AI analysis data: {e}")
                except Exception as e:
                    st.error(f"Error processing item data: {e}")

            except Exception as e:
                st.error(f"Error in style advisor: {e}")
    else:
        st.info("Add some items to your wardrobe to get personalized style advice!")

def fashion_agent(tracker):
    st.title("🤖 SambaFit")
    
    st.markdown("Welcome to SambaFit! Ask me to create an outfit for the day!")

    model_data = []
    for item in tracker.database['items']:
        model_data.append({item['id']: item['ai_analysis']})

    # Chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat history
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            if isinstance(message["content"], list):  # If the bot's response contains images
                for img_b64 in message["content"]:
                    # Convert and display the image
                    image = tracker.base64_to_image(img_b64)
                    st.image(image, caption="Suggested Outfit", use_column_width=True)
            else:
                st.markdown(f"**SambaFit:** {message['content']}")

    # Callback function to process input
    def handle_input():
        # Retrieve user input
        user_input = st.session_state.get("unique_user_input", "")

        if user_input:
            # Add user's message to chat history
            st.session_state["messages"].append({"role": "user", "content": user_input})

            # Generate a response (placeholder for now)
            # Replace with API call to SambaFit AI when integrated
            response = generate_response(user_input, model_data)
            images_res = []
            for item in response:
                # Grab the key
                key = list(item.keys())[0]
                b64 = get_base_64_by_id(tracker, key)
                if b64 is not None:
                    images_res.append(b64)

            print(images_res)
            # Add the images to the bot's response in the chat
            st.session_state["messages"].append({"role": "bot", "content": images_res})

            # Display success message
            st.success("Response successfully updated with suggested outfits!")

            # Clear the input box
            st.session_state["unique_user_input"] = ""

    # User input box with a unique key
    st.text_input(
        "Type details here (weather, occasion etc):",
        key="unique_user_input",  # Ensure the key is unique
        on_change=handle_input,
    )


def get_base_64_by_id(tracker, id):
    for item in tracker.database['items']:
        if str(item["id"]) == id:
            return item['image']
    return None

def generate_response(user_input, data):
    print("data: ",data)
    model1_res = model1_tokenize_prompt(user_input)
    print("tokens: ", model1_res)
    overall_res = model2_select_items(model1_res, data)
    print("overall: ",overall_res)
    return overall_res




def initialize_database():
    """Initialize the database file if it doesn't exist or is empty"""
    database_path = 'clothing_database.json'
    initial_data = {
        "items": [],
        "outfits": [],
        "listings": []
    }
    
    try:
        if not os.path.exists(database_path):
            with open(database_path, 'w') as file:
                json.dump(initial_data, file)
        else:
            # Try to load existing database
            try:
                with open(database_path, 'r') as file:
                    data = json.load(file)
                    if not isinstance(data, dict) or not all(key in data for key in initial_data.keys()):
                        raise ValueError("Invalid database structure")
            except (json.JSONDecodeError, ValueError):
                # If file is corrupt, reinitialize it
                with open(database_path, 'w') as file:
                    json.dump(initial_data, file)
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        # Ensure we have a valid database even if something goes wrong
        with open(database_path, 'w') as file:
            json.dump(initial_data, file)


def marketplace_tab(tracker, email_notifier):
    st.subheader("🛍️ Marketplace Listings")



    # Create tabs for "Your Listings" and "Others' Listings"
    tab1, tab2 = st.tabs(["Your Listings", "Others' Listings"])

    with tab1:
        # Get items that haven't been worn for 8+ days
        current_date = datetime.now().date()
        listed_items = []

        # First get existing listings
        listed_items.extend(tracker.get_listings())

        # Then check for new items that should be listed
        for item in tracker.database["items"]:
            if "last_worn" not in item:
                continue  # Skip items without last_worn date

            last_worn_date = datetime.fromisoformat(item["last_worn"]).date()
            days_since = (current_date - last_worn_date).days

            # If item should be listed and isn't already
            if days_since >= 8 and not any(listing["id"] == item["id"] for listing in listed_items):
                if tracker.move_to_listings(item["id"], "items"):
                    listed_items = tracker.get_listings()  # Refresh listings

        if listed_items:
            st.write(f"📦 {len(listed_items)} Items Available")

            for item in listed_items:
                listing_key = f"listing_content_{item['id']}"

                with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if 'image' in item:
                            image = tracker.base64_to_image(item['image'])
                            if image:
                                st.image(image, use_column_width=True)

                        st.markdown("**Item Details:**")
                        st.markdown(f"- Type: {item['type']}")
                        st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")
                        st.markdown(f"- Condition: {item.get('condition', 'Not specified')}")

                        # Handle case where neither date_listed nor last_worn exists
                        try:
                            if 'date_listed' in item:
                                listed_date = datetime.fromisoformat(item['date_listed'])
                            elif 'last_worn' in item:
                                listed_date = datetime.fromisoformat(item['last_worn'])
                            else:
                                listed_date = datetime.now()

                            days_listed = (current_date - listed_date.date()).days
                            st.markdown(f"- Listed: {days_listed} days ago")
                        except Exception as e:
                            st.markdown("- Recently listed")

                    with col2:
                        if listing_key not in st.session_state:
                            with st.spinner("Creating listing description..."):
                                listing_content = email_notifier.generate_listing_content(item)
                                if listing_content:
                                    st.session_state[listing_key] = listing_content
                                else:
                                    st.session_state[listing_key] = "Error generating listing content."

                        st.markdown(st.session_state[listing_key])

                        col3, col4 = st.columns([1, 1])
                        with col3:
                            if st.button("Refresh Listing", key=f"refresh_{item['id']}"):
                                with st.spinner("Regenerating listing..."):
                                    new_content = email_notifier.generate_listing_content(item)
                                    if new_content:
                                        st.session_state[listing_key] = new_content
                                        st.success("Listing refreshed!")

                        with col4:
                            if st.button("Remove Listing", key=f"remove_{item['id']}"):
                                if tracker.remove_from_listings(item['id']):
                                    if listing_key in st.session_state:
                                        del st.session_state[listing_key]
                                    st.success("Item removed from marketplace!")
                                    time.sleep(0.5)
                                    st.rerun()
        else:
            st.info("👋 No items currently listed! Items unworn for 8+ days will appear here automatically.")

    # with tab2:
        #     st.write("🔍 This section will show marketplace listings from other users.")
        #     # Dropdown menu for filtering
        #     filter_option = st.selectbox("Filter listings:", ["Off", "By Preference"])

        #     if filter_option == "Off":
        #         st.write("🔍 All listings are displayed here.")
        #     elif filter_option == "By Preference":
        #         st.write("🔍 Listings filtered by your preferences will appear here.")

    #     st.info("Feature coming soon!")
    with tab2:
        by_preference = False
        st.write("🔍 This section will show marketplace listings from other users.")
        # Dropdown menu for filtering
        filter_option = st.selectbox("Filter listings:", ["Off", "By Preference"])
        if filter_option == "Off":
            st.write("🔍 All listings are displayed here.")
            by_preference = False
        elif filter_option == "By Preference":
            st.write("🔍 Listings filtered by your preferences will appear here.")
            by_preference = True
        marketplace = Marketplace()


        # Get all items from the marketplace database
        listed_items = marketplace.get_all_items()

        if by_preference:
            with open('clothing_database.json', 'r') as file:
                data = json.load(file)
                contents = data.get('items', [])

            if not contents and by_preference:
                st.info("Your wardrobe is empty! Add some items to get personalized insights.")
                return

            # Find items with min and max wear count
            min_view = float('inf')
            max_view = -1
            smallest_des = None
            largest_des = None

            for item in contents:
                wear_count = item.get('wear_count', 0)
                if 'ai_analysis' in item:
                    if wear_count < min_view:
                        smallest_des = item['ai_analysis']
                        min_view = wear_count
                    if wear_count > max_view:
                        largest_des = item['ai_analysis']
                        max_view = wear_count

            if not smallest_des or not largest_des:
                st.warning("Not enough analyzed items to generate insights.")
                return


            with st.spinner("Analyzing wardrobe preferences..."):
                result = decide_preference(largest_des, smallest_des)
                results_list = json.loads(result)
                print("Res_list: ",results_list)

            # Extract liked and disliked traits from the user's wardrobe analysis
            liked_characteristics = results_list[0]
            disliked_characteristics = results_list[1]

            # Create a filtered list of items based on the user's preferences
            filtered_items = []
            for item in listed_items:
                try:
                    # Get `ai_analysis` as a raw string
                    ai_analysis_raw = item.get("ai_analysis", "").strip()

                    # Skip if `ai_analysis` is empty
                    if not ai_analysis_raw:
                        st.warning(f"Item {item.get('name', 'Unnamed')} has no valid AI analysis.")
                        continue

                    # Pass `ai_analysis` directly as the item_characteristics to the model
                    if decide_match(liked_characteristics, disliked_characteristics, ai_analysis_raw):
                        filtered_items.append(item)
                except ValueError as e:
                    st.error(f"Error analyzing item {item.get('name', 'Unnamed')}: {e}")

            # Display filtered items
            if filtered_items:
                st.write(f"🎯 {len(filtered_items)} Items Match Your Preferences")

                for item in filtered_items:
                    listing_key = f"listing_content_{item['id']}"

                    with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            if 'image' in item:
                                # Display the item's image
                                image = marketplace.base64_to_image(item['image'])
                                if image:
                                    st.image(image, use_column_width=True)

                            st.markdown("**Item Details:**")
                            st.markdown(f"- Type: {item.get('type', 'Unknown')}")
                            st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")

                        with col2:
                            listing_content = f"This item matches your preferences with characteristics: {ai_analysis_raw}"
                            st.markdown(listing_content)

                            if st.button("Buy", key=f"buy_{item['id']}"):
                                # Remove the item from the marketplace
                                if marketplace.remove_item(item['id']):
                                    st.success(f"Item '{item.get('name', 'Unnamed')}' purchased successfully!")
                                    time.sleep(0.5)
                                    st.rerun()  # Refresh the UI to reflect the change
            else:
                st.info("No items match your preferences.")




        else:
            if listed_items:
                st.write(f"📦 {len(listed_items)} Items Available")

                for item in listed_items:
                    listing_key = f"listing_content_{item['id']}"

                    with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            if 'image' in item:
                                # Display the item's image
                                image = marketplace.base64_to_image(item['image'])  # Assuming base64_to_image is available
                                if image:
                                    st.image(image, use_column_width=True)

                            st.markdown("**Item Details:**")
                            st.markdown(f"- Type: {item['type']}")
                            st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")
                            st.markdown(f"- Condition: {item.get('condition', 'Not specified')}")

                            # Handle case where neither date_listed nor last_worn exists
                            try:
                                if 'date_listed' in item:
                                    listed_date = datetime.fromisoformat(item['date_listed'])
                                elif 'last_worn' in item:
                                    listed_date = datetime.fromisoformat(item['last_worn'])
                                else:
                                    listed_date = datetime.now()

                                days_listed = (datetime.now().date() - listed_date.date()).days
                                st.markdown(f"- Listed: {days_listed} days ago")
                            except Exception as e:
                                st.markdown("- Recently listed")

                        with col2:
                            if listing_key not in st.session_state:
                                with st.spinner("Creating listing description..."):
                                    listing_content = email_notifier.generate_listing_content(item)
                                    if listing_content:
                                        st.session_state[listing_key] = listing_content
                                    else:
                                        st.session_state[listing_key] = "Error generating listing content."

                            st.markdown(st.session_state[listing_key])

                            col3, col4 = st.columns([1, 1])
                            with col3:
                                if st.button("Claim", key=f"claim_{item['id']}"):
                                    # Remove the item from the marketplace
                                    if marketplace.remove_item(item['id']):
                                        st.success(f"Item '{item.get('name', 'Unnamed')}' claimed successfully!")

                                        # Add the item to the wardrobe
                                        claimed_image = marketplace.base64_to_image(item["image"])
                                        success = tracker.add_new_item_sync(
                                            claimed_image,
                                            item["type"],
                                            is_outfit=False,  # Assuming it's not a full outfit
                                            name=item.get("name", item["type"])
                                        )

                                        if success:
                                            st.success("Item added to your wardrobe!")
                                        else:
                                            st.error("Failed to add the item to your wardrobe.")
            else:
                st.info("👋 No items currently listed! Items will appear here automatically.")





    
def initialize_notification_state():
    if 'notification_state' not in st.session_state:
        st.session_state.notification_state = {
            'unworn_items': None,
            'show_send_button': False,
            'sending_email': False
        }
def initialize_camera_state():
    if 'camera_initialized' not in st.session_state:
        st.session_state.camera_initialized = False
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'first_run' not in st.session_state:
        st.session_state.first_run = True
    if 'image_processed' not in st.session_state:
        st.session_state['image_processed'] = False
def edit_wardrobe_tab(tracker):
    st.subheader("Edit Wardrobe Items")
    
    all_items = (
        [{"collection": "items", **item} for item in tracker.database["items"]] +
        [{"collection": "outfits", **outfit} for outfit in tracker.database["outfits"]]
    )
    
    if not all_items:
        st.info("Your wardrobe is empty! Add some items first.")
        return
        
    for item in all_items:
        with st.expander(f"{item.get('name', item['type'])}"):
            with st.form(key=f"form_{item['id']}_{item['collection']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if 'image' in item:
                        image = tracker.base64_to_image(item['image'])
                        if image:
                            st.image(image, width=200)
                    
                    new_wear_count = st.number_input(
                        "Times worn",
                        min_value=0,
                        value=item.get('wear_count', 0),
                        key=f"wear_count_{item['id']}_{item['collection']}"
                    )
                
                with col2:
                    new_last_worn = st.date_input(
                        "Last worn date",
                        value=datetime.fromisoformat(item["last_worn"]).date(),
                        max_value=datetime.now().date(),
                        key=f"last_worn_{item['id']}_{item['collection']}"
                    )
                    
                    days_since = (datetime.now().date() - new_last_worn).days
                    days_remaining = max(0, 7 - days_since)
                    st.warning(f"⏳ {days_remaining} days remaining")
                
                # Place 'Update' and 'Delete' buttons inside the form
                submitted = st.form_submit_button("Update")
                delete_clicked = st.form_submit_button("Delete Item")
                
                if submitted:
                    success = tracker.update_item(
                        item['id'],
                        item['collection'],
                        datetime.combine(new_last_worn, datetime.min.time()).isoformat(),
                        int(new_wear_count)
                    )
                    if success:
                        st.success("✅ Item updated!")
                        
                        # Check if item should be moved to marketplace
                        if days_since >= 8:
                            tracker.move_to_listings(item['id'], item['collection'])
                            st.info("📦 Item moved to marketplace due to inactivity")
                        
                if delete_clicked:
                    collection = item['collection']
                    tracker.database[collection] = [
                        x for x in tracker.database[collection] 
                        if x['id'] != item['id']
                    ]
                    tracker.save_database()
                    st.success("🗑️ Item deleted!")


def main():
    initialize_email_settings()
    initialize_notification_state()
    initialize_camera_state()  # Add this line
    initialize_database()
    st.title("VESTIQUE - Smart Wardrobe Assistant")
    
    feature_extractor = FeatureExtractor()
    tracker = WardrobeTracker(feature_extractor)
    email_notifier = EmailNotifier()
    if 'style_advisor' not in st.session_state:
        st.session_state.style_advisor = StyleAdvisor(SAMBANOVA_API_KEY)
    # Sidebar controls
    with st.sidebar:
        st.subheader("Settings")
        mode = st.radio(
            "Capture Mode",
            ["Single Item", "Full Outfit"],
            help="Choose whether to capture a single clothing item or a full outfit"
        )
        
        if st.button("Load Demo Data"):
            tracker.add_demo_data()
        
        debug_mode = st.checkbox("Debug Mode")
        st.session_state['debug_mode'] = debug_mode

        # Email Settings in Sidebar
        st.divider()
        st.subheader("📧 Email Settings")
        with st.expander("Configure Email"):
            sender_email = st.text_input(
                "Gmail Address", 
                value=st.session_state.sender_email,
                help="Enter the Gmail address you want to send notifications from"
            )
            
            email_password = st.text_input(
                "App Password", 
                type="password",
                value=st.session_state.email_password,
                help="Enter your Gmail App Password (Not your regular Gmail password). Get it from Google Account -> Security -> 2-Step Verification -> App passwords"
            )
            
            if st.button("Save Email Settings"):
                if '@gmail.com' not in sender_email:
                    st.error("Please enter a valid Gmail address")
                elif len(email_password) != 16:
                    st.error("App Password should be 16 characters. Please check your Google App Password")
                else:
                    st.session_state.sender_email = sender_email
                    st.session_state.email_password = email_password
                    st.session_state.email_configured = True
                    st.success("✅ Email settings saved!")

        # Default reset period
        st.divider()
        st.subheader("Default Reset Period")
        new_reset_period = st.number_input(
            "Days until reset for new items", 
            min_value=1, 
            max_value=30, 
            value=tracker.reset_period
        )
        if new_reset_period != tracker.reset_period:
            tracker.reset_period = new_reset_period
            st.success(f"Default reset period updated to {new_reset_period} days!")

    # Main content
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Capture", "My Wardrobe", "Edit Wardrobe", 
    "Notifications", "Preferences", "Marketplace", "Style Advisor", "SambaFit"
        ])
    
    with tab1:
        
            st.subheader("Capture New Item" if mode == "Single Item" else "Capture Outfit")
            # Fix for first run
            # Initialize session state variables
            if 'current_image' not in st.session_state:
                st.session_state['current_image'] = None
            if 'image_status' not in st.session_state:
                st.session_state['image_status'] = None
            if 'image_item' not in st.session_state:
                st.session_state['image_item'] = None
            if 'image_similarity' not in st.session_state:
                st.session_state['image_similarity'] = None
            # Custom CSS to force the camera layout
            st.markdown("""
                <style>
                /* Main camera container */
                .stCamera {
                    background-color: #1E1E1E !important;
                    border-radius: 10px !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    width: 640px !important;
                    height: 480px !important;
                }
                
                /* Video feed */
                .stCamera > video {
                    width: 100% !important;
                    height: 100% !important;
                    object-fit: cover !important;
                }
                
                /* Captured image */
                .stCamera > img {
                    width: 100% !important;
                    height: 100% !important;
                    object-fit: contain !important;
                    background-color: #1E1E1E !important;
                }
                
                /* Clear photo button section */
                .stCamera > div {
                    position: absolute !important;
                    bottom: 0 !important;
                    width: 100% !important;
                    background-color: rgba(0,0,0,0.7) !important;
                    padding: 8px !important;
                    border-radius: 0 0 10px 10px !important;
                }

                /* Center the camera in the page */
                [data-testid="stHorizontalBlock"] {
                    justify-content: center !important;
                    background-color: transparent !important;
                }

                /* Remove any extra padding/margin */
                .stApp {
                    margin: 0 auto !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Camera input in center of page
            camera = st.camera_input(
                "Take a photo" if mode == "Single Item" else "Take a photo of your outfit",
                key="camera_input",
                label_visibility="hidden"
            )
            if camera is not None:
                if st.session_state['current_image'] is None:
                    image = Image.open(camera)
                    st.session_state['current_image'] = image

                    # Process image
                    status, item, similarity = tracker.process_image(
                        image, 
                        is_outfit=(mode == "Full Outfit")
                    )

                    st.session_state['image_status'] = status
                    st.session_state['image_item'] = item
                    st.session_state['image_similarity'] = similarity
                else:
                    image = st.session_state['current_image']
                    status = st.session_state['image_status']
                    item = st.session_state['image_item']
                    similarity = st.session_state['image_similarity']

                # Now, display based on status
                if status == "existing":
                    st.success(f"✅ Found matching {item['type']}! (Similarity: {similarity:.3f})")
                    if 'image' in item:
                        matched_image = tracker.base64_to_image(item['image'])
                        if matched_image:
                            st.image(matched_image, caption="Matched Item", use_column_width=True)
                    
                    if debug_mode:
                        st.write("Match details:", item)
                        
                elif status == "too_soon":
                    reset_period = item.get('reset_period', tracker.reset_period)
                    days_since = (datetime.now() - datetime.fromisoformat(item["last_worn"])).days
                    days_remaining = max(0, reset_period - days_since)
                    st.warning(f"⚠️ This {item['type']} needs {days_remaining} more days to reset!")
                    
                    if 'image' in item:
                        matched_image = tracker.base64_to_image(item['image'])
                        if matched_image:
                            st.image(matched_image, caption="Recently Worn Item", use_column_width=True)
                    
                elif status == "new":
                    st.info("🆕 New item detected!")
                    st.image(image, caption="Captured Image", use_column_width=True)
                    
                    if mode == "Single Item":
                        item_type = st.selectbox(
                            "What type of clothing is this?",
                            list(tracker.clothing_categories.keys())[:-1],
                            key='item_type_selectbox'
                        )
                        name = st.text_input("Give this item a name (optional):", 
                                            value=f"My {item_type}", key='item_name_input')
                    else:
                        item_type = "Full Outfit"
                        name = st.text_input("Give this outfit a name:", "My New Outfit", key='outfit_name_input')
                    
                    if st.button("Add to Wardrobe"):
                        try:
                            with st.spinner("Adding item to wardrobe..."):
                                success = tracker.add_new_item(
                                    image,
                                    item_type,
                                    is_outfit=(mode == "Full Outfit"),
                                    name=name
                                )
                                
                            if success:
                                st.success("✅ Added to wardrobe!")
                                # Reset the session state
                                st.session_state['current_image'] = None
                                st.session_state['image_status'] = None
                                st.session_state['image_item'] = None
                                st.session_state['image_similarity'] = None
                                
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            # Still try to add the item without AI analysis
                            fallback_success = tracker.add_new_item_sync(
                                image,
                                item_type,
                                is_outfit=(mode == "Full Outfit"),
                                name=name
                            )
                            if fallback_success:
                                st.warning("⚠️ Added to wardrobe without AI analysis")
                            # Reset the session state
                            st.session_state['current_image'] = None
                            st.session_state['image_status'] = None
                            st.session_state['image_item'] = None
                            st.session_state['image_similarity'] = None

            else:
                # Reset session state when no camera input
                st.session_state['current_image'] = None
                st.session_state['image_status'] = None
                st.session_state['image_item'] = None
                st.session_state['image_similarity'] = None
    
    with tab2:
        tracker.display_wardrobe_grid()
        
    with tab3:
        edit_wardrobe_tab(tracker)

    with tab4:
        st.subheader("📧 Email Notifications")
        
        recipient_email = st.text_input("Your Email Address")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("Check Unworn Items", use_container_width=True):
                st.write(f"Total items in database: {len(tracker.database['items'])}")
                unworn_items = email_notifier.check_unworn_items(tracker)
                st.session_state.notification_state['unworn_items'] = unworn_items
                st.session_state.notification_state['show_send_button'] = True
                
            # Display unworn items if they exist in session state
            if st.session_state.notification_state['unworn_items']:
                unworn_items = st.session_state.notification_state['unworn_items']
                st.warning(f"Found {len(unworn_items)} items unworn for 7+ days")
                
                with st.expander("View Unworn Items"):
                    for item in unworn_items:
                        st.write(f"• {item.get('name', item['type'])} - Last worn: {item['last_worn']}")
                
                if st.session_state.notification_state['show_send_button']:
                    send_col1, send_col2 = st.columns([3, 1])
                    with send_col1:
                        if st.button("📧 Send Reminder Email", use_container_width=True):
                            if not recipient_email:
                                st.error("Please enter your email address first")
                            else:
                                status_placeholder = st.empty()
                                progress_bar = st.progress(0)
                                
                                try:
                                    # Update progress
                                    status_placeholder.text("Generating email content...")
                                    progress_bar.progress(25)
                                    
                                    # Generate content first
                                    email_content = email_notifier.generate_personalized_content(unworn_items)
                                    
                                    # Show preview
                                    progress_bar.progress(50)
                                    status_placeholder.text("Sending email...")
                                    
                                    with st.expander("📧 Preview Generated Email"):
                                        st.text(email_content)
                                    
                                    # Send email
                                    success = email_notifier.send_notification(recipient_email, unworn_items)
                                    progress_bar.progress(100)
                                    
                                    if success:
                                        status_placeholder.success("✅ Email sent successfully!")
                                        st.balloons()
                                    else:
                                        status_placeholder.error("Failed to send email")
                                    
                                    # Keep status visible for a moment
                                    time.sleep(2)
                                    
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                finally:
                                    # Clean up progress elements
                                    progress_bar.empty()
            
            elif st.session_state.notification_state.get('unworn_items') == []:
                st.success("All items in your wardrobe are being used regularly!")
        
        with col2:
            if st.button("Send Test Email", use_container_width=True):
                if not recipient_email:
                    st.error("Please enter your email address first")
                else:
                    with st.spinner("Sending test email..."):
                        test_items = [{
                            "name": "Test Item",
                            "type": "T-Shirt",
                            "last_worn": datetime.now().isoformat(),
                            "wear_count": 1
                        }]
                        success = email_notifier.send_notification(recipient_email, test_items)
                        if success:
                            st.success("Test email sent!")
                            with st.expander("📧 Test Email Preview"):
                                st.text(email_notifier.generate_personalized_content(test_items))
    import json

    with tab5:
        preferences_tab()


    with tab6:
        marketplace_tab(tracker, email_notifier)

     

    with tab7:
        style_advisor_tab(tracker)

    with tab8:
        fashion_agent(tracker)
    

if __name__ == "__main__":
    main()