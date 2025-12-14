# Friendly Feud Widget

## Description of features
features: start new round, make guess, reveal one, and reveal all. 

When we start a new round, 10 flippable cards are shown, all 'face down' (aka 'unrevealed'). The cards are rectanges containing text, each with the same background image. A score counter is shown in the bottom right hand corner, kind of like an old-school, oval-shaped score counter from old game show games. As users guess the answers, the cards are revealed, showing their answers and incrementing the total score for the round. A configurable maximum number of incorrect guesses can be made before the round ends and the answers are all revealed.

The start new round feature takes an input of n (n between 1-10 inclusive) 'answers' and n lists of synonms (one list of synonyms for each answer, can be length zero) that users try to guess during the round. Each answer has an integer point value.  The cards are arranged in two columns, sorted from greatest point value to least value going down the first column, then going down the second column. The program controls the state of the 10 cards from 'unrevealed' to 'reveled'. The cards begin in the unrevealed state at the start of the round and are revealed as correct guesses are made, which shows the answer on the reverse side of the card using a card flip animation. 

THe make guess feature takes a 'guess' string as a parameter. Answers are buffered before being evaluated, and are evaluated at a parametrized frequency (plus or minus a parametrized random variation). On evaluation, the guess string is compared against the list of answers and each of the words in each answer's  acceptable synonym list. If any of the answers or synonyms match (case insensitive), then the matching card is reveled and a 'ding' sound is played. THe total score is incremented by the point value of the answer, and the guessing player's round score is also incremented by the answer's point value. If the guess doesn't match any answers or synonyms, then a strike is added to the strike counter, a buzzer sound is played, and a number of huge X's matching the updated number of strikes are shown on the screen (for a parametrized amount of time).  If the maximum number of strikes are reached (Default is 3) then the game also runs the 'reveal all' feature automatically after it finished playing the buzzer sound and showing/hiding the X's.

The 'reveal one' feature revels the unrevealed card with the lowest point value. If all cards are already revealed, nothing happens and the feature returns. If a card is revealed, the ding sound is played at the same time. The total score is not incremented in this case.



# Extra considerations
widget-element structure: Cards should each be a separate element. 

All cards should be managed separately, not as one element. 

Score counter is a separate element of type text, which has a background on whch the text is centered and aligned in the middle.

strike x's are a text element and the number of x's inside of the text element is used to indicate the number of strikes. The font of the X"s is very large, big enough to cover 30 % of the screen. Red text.

the answers in the sentiments should be passed as a single list of dictionaries, unless there is a simpler syntax since the user will enter this data through the widget's properties modal in the admin UX.

maximum number of strikes and the guess evaluation frequency are not parameters of the feature, they are parameters of the widget. 

everything should be managed inside of the widget, including the guest buffer and the evaluation frequency. Nothing in this logic needs to be exposed to the API.

widget also keeps track of the player which made each guess and tracks each player's score on a per round basis.  

the overlays should handle the card flip animation and display logic based on the element state. For example, the widget logic changes the state of a card to flipped then the overlay animates the card flip and shows the other side. We will need to create a new type of element that is a card type 


FriendlyFeud Widget Design Summary
Widget Class
Name: FriendlyFeudWidget
widget_class: "FriendlyFeudWidget"
display_name: "Friendly Feud"
Elements
Cards: 1–10 separate Elements of new type CARD
Each card: answer text, synonyms, point value, revealed state, face-down asset, face-up asset (answer text)
Score Counter: Element of type TEXT (shows score as text)
Strike X's: Element of type TEXT (shows "X" * strikes)
Audio: THree Elements of type AUDIO (ding, buzzer, start round, end round)
Widget Parameters
max_strikes: int (default 3)
guess_eval_frequency: float (seconds, e.g., 1.5)
guess_eval_jitter: float (seconds, e.g., 0.5)
Features
start_new_round: Accepts a list of dicts: [{"answer": str, "synonyms": [str], "points": int}, ...]
make_guess: Accepts guess: str and player: str; guesses are buffered and evaluated at the configured frequency (+/- jitter)
reveal_one: Reveals the unrevealed card with the lowest point value
reveal_all: Reveals all unrevealed cards
State Management
Widget manages guess buffer, evaluation timing, and per-player scores for the round
Player scores tracked per round (dict: user -> score)
Overlay handles card flip animation and X display based on element state
Widget only broadcasts deltas (e.g., card revealed, score updated)
ElementType
New ElementType.CARD needed (with two faces: face-down asset, face-up answer)
Card element role, media:
background-front (could be image or video or blank)
background-back (could be image or video or blank)
text-front (text)
text-back (text)
flip-sound (sound)
after-flip-sound (sound) (a sound played after the card is set from unrevealed to revealed)

Has two media (front and back media) which serve as background images for each side, and the answer and  point value as text on the other side., and revealed state in properties
Open Decisions
Synonym matching: like the answer matching, should be case-insensitive and spelling can be fuzzy (default: fuzzy spelling)
Card arrangement: Overlay shows elements, widget provides all card data to appropriate elements. 10 cards are created on instantiation of the widget, and they are ordered in the overlay. THen the answers are sorted by the widget when the round is started and the cards are updated appropriately. The widget maps the answers to the UI positions so it can lookup which card corresponds to which answer.


Element type and structure: CARD is a new ElementType, and the text and state are stored in properties in JSON.

Create 10 elements by default, and hide/show cards until there are no unusued cards shown  (cards with no answer provided) on start of the round.

Use a library such as rapidfuzz or fuzzywuzzy, you choose which. Threshold is a configurable parameter, default 95%. Case insensitive.

Reveal all timing: When the reveal all feature is executed and, the widget needs to reveal answers  at a parameterized frequency. This can be done in a simple for or while loop, where we iterate through all answers from the lowest point to the highest point and reveal the answer if it has not yet been revealed.

Async guess buffering: once the 'start round' feature is active, the program ends up in a main loop which: checks for a guess in the queue, evaluates the guess, checks if the game is finished, and waits a parametrized amount of time to repeat the cycle. Use a finished round flag, which can be set when all answers are revealed, or set when the reveal-all feature has been initiated. If the game is discovered to be finished, break the loop, wait a parametrized amount of time, and fade away elements if the 'fade-round-after-end' parameter is set true.

ADDING PLAYER MODULE