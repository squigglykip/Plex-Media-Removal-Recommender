# Weightings for removal score calculation
# Ensure that the sum of all weights equals 1.0 (or 100%) for the scoring to work correctly.
# Adjust these values based on the importance of each factor in your decision-making process.

PLAY_COUNT_WEIGHT = 0.3  # Weight for play count
RATING_WEIGHT = 0.3      # Weight for rating
AGE_WEIGHT = 0.2         # Weight for age
SIZE_WEIGHT = 0.2        # Weight for file size

# Example: If you want to prioritize play count more, you might set:
# PLAY_COUNT_WEIGHT = 0.4
# RATING_WEIGHT = 0.3
# AGE_WEIGHT = 0.2
# SIZE_WEIGHT = 0.1
# Just ensure the total is 1.0