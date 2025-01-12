from rest_framework import serializers


class AhjoCallbackSerializer(serializers.Serializer):
    message = serializers.CharField()
    requestId = serializers.UUIDField(format="hex_verbose")
    caseId = serializers.CharField()
    caseGuid = serializers.UUIDField(format="hex_verbose")

    # You can add additional validation here if needed
    def validate_message(self, message):
        # Example of custom field validation
        if message not in ["Success", "Failure"]:
            raise serializers.ValidationError("Invalid message value.")
        return message
