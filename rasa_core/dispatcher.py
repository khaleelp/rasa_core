from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from collections import namedtuple

import typing
from typing import Text, List, Dict, Any

from rasa_core.channels import OutputChannel
from rasa_core.nlg import NaturalLanguageGenerator

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from rasa_core.trackers import DialogueStateTracker


class Element(dict):
    __acceptable_keys = ['title', 'item_url', 'image_url',
                         'subtitle', 'buttons']

    def __init__(self, *args, **kwargs):
        kwargs = {key: value
                  for key, value in kwargs.items()
                  if key in self.__acceptable_keys}

        super(Element, self).__init__(*args, **kwargs)


# Makes a named tuple with entries text and data
BotMessage = namedtuple("BotMessage", "text data metadata")


class Button(dict):
    pass


class Dispatcher(object):
    """Send messages back to user"""

    def __init__(self, sender_id, output_channel, nlg):
        # type: (Text, OutputChannel, NaturalLanguageGenerator) -> None

        self.sender_id = sender_id
        self.output_channel = output_channel
        self.nlg = nlg
        self.latest_bot_messages = []

    def utter_response(self, message, tracker = None, domain = None):
        # type: (Dict[Text, Any]) -> None
        """Send a message to the client."""

        bot_message = BotMessage(text=message.get("text"),
                                 data={"elements": message.get("elements"),
                                       "buttons": message.get("buttons"),
                                       "attachment": message.get("image")},
                                 metadata=message.get("domain_stuff"))
        print("~~~~~~~~~~~~~~~~~~~Bleh~~~~~~~~~~~")
        print(bot_message.metadata)
        print(message)
        self.latest_bot_messages.append(bot_message)
        self.output_channel.send_response(self.sender_id, message, tracker = tracker, domain = domain)

    def utter_message(self, text):
        # type: (Text) -> None
        """"Send a text to the output channel"""
        # Adding the text to the latest bot messages (with no data)
        bot_message = BotMessage(text=text,
                                 data=None)

        self.latest_bot_messages.append(bot_message)
        self.output_channel.send_text_message(self.sender_id, text)

    def utter_custom_message(self, *elements):
        # type: (*Dict[Text, Any]) -> None
        """Sends a message with custom elements to the output channel."""

        bot_message = BotMessage(text=None,
                                 data={"elements": elements})

        self.latest_bot_messages.append(bot_message)
        self.output_channel.send_custom_message(self.sender_id, elements)

    def utter_button_message(self, text, buttons, **kwargs):
        # type: (Text, List[Dict[Text, Any]], Any) -> None
        """Sends a message with buttons to the output channel."""
        # Adding the text and data (buttons) to the latest bot messages
        bot_message = BotMessage(text=text,
                                 data={"buttons": buttons})

        self.latest_bot_messages.append(bot_message)
        self.output_channel.send_text_with_buttons(self.sender_id, text,
                                                   buttons,
                                                   **kwargs)

    def utter_attachment(self, attachment):
        # type: (Text) -> None
        """Send a message to the client with attachments."""
        bot_message = BotMessage(text=None,
                                 data={"attachment": attachment})

        self.latest_bot_messages.append(bot_message)
        self.output_channel.send_image_url(self.sender_id, attachment)

    # TODO: deprecate this function
    def utter_button_template(self,
                              template,  # type: Text
                              buttons,  # type: List[Dict[Text, Any]]
                              tracker,  # type: DialogueStateTracker
                              silent_fail=False,  # type: bool
                              **kwargs   # type: Any
                              ):
        # type: (...) -> None
        """Sends a message template with buttons to the output channel."""

        message = self._generate_response(template,
                                          tracker,
                                          silent_fail,
                                          **kwargs)
        if not message:
            return

        if "buttons" not in message:
            message["buttons"] = buttons
        else:
            message["buttons"].extend(buttons)
        self.utter_response(message, tracker = tracker)

    def utter_template(self,
                       template,  # type: Text
                       tracker,  # type: DialogueStateTracker
                       domain = None,
                       silent_fail=False,  # type: bool
                       **kwargs  # type: Any
                       ):
        # type: (...) -> None
        """"Send a message to the client based on a template."""
        print("~~~~~~~~~~~~~~~Something~~~~~~~~~~~~~~~")
        print(domain.action_names)
        print({"entities" : domain.entities})
        print(domain.intent_properties)
        print(domain.form_names)
        print({"slots" : domain.slots})
        print(domain.restart_intent)
        print(domain.store_entities_as_slots)
        print(domain.templates)
        print(domain.user_actions)
        print(tracker.slots)
        print(tracker.events)
        print(tracker.active_form)
        print(tracker.latest_action_name)
        print(tracker.followup_action)
        print(tracker.sender_id)
        print(tracker.latest_bot_utterance)
        print(tracker.latest_message)
        print("~~~~~~~~~~~~~~~SomethingENDS~~~~~~~~~~~~~~~")
        message = self._generate_response(template,
                                          tracker,
                                          silent_fail,
                                          **kwargs)

        if not message:
            return

        self.utter_response(message, tracker = tracker, domain = domain)

    def _generate_response(
        self,
        template,  # type: Text
        tracker,  # type: DialogueStateTracker
        silent_fail=False,  # type: bool
        **kwargs  # type: Any
    ):
        # type: (...) -> Dict[Text, Any]
        """"Generate a response."""

        message = self.nlg.generate(template, tracker,
                                    self.output_channel.name(),
                                    **kwargs)

        if message is None and not silent_fail:
            logger.error("Couldn't create message for template '{}'."
                         "".format(template))

        return message
