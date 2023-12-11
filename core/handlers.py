class InvitationHandler:
    def get_user_from_email(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
    def validate(self, user: User, invitation: Invitation):
        if user.email != invitation.to_email:
            raise PermissionDenied(detail="This invitation is not ment for you.")

        delta = timezone.now() - invitation.created_date
        if delta.days > invitation.expiration:
            raise PermissionDenied(detail="This invitation has expired.")
        
        if invitation.is_accepted or invitation.is_rejected:
            raise PermissionDenied(detail="This invitation has expired.")
        
    def accept(self, user: User, invitation: Invitation):
        self.validate(user, invitation)        
        Member.add(invitation.organization,user)

        invitation.is_accepted = True
        invitation.save()

    def reject(self, user: User, invitation: Invitation):
        self.validate(user, invitation)

        invitation.is_rejected = True
        invitation.save()