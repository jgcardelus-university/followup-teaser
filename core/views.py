"""
View:

Extension of the django rest framework's API base view that
add pagination functionality and allows to retrieve
the view's context

SecureExtendedView:

Extension of the View which handles requests different based
on the user's authentication. For authenticated users, the
view will call the methods get, put, post, delete and it will
call the methods get_public, put_public, post_public, etc. for
un-authenticated users.

ModelView:

Extension of View which adds extra functionality (filtering, 
retrieve objects from url params, etc.) for views
that are tied to a model.

OrganizationModelView:

Extension of ModelView, for models that belong to an organization
(like Members, Groups, Apartments, Reviews, Follow Ups).

It verifies that the resource being accessed does indeed belong
to the organization, it gets information on the member accessing the
information and checks the permissions of that user.

It also ensures that information outside the organization cannot be 
accessed.
"""


class View(RestFrameworkAPIView):
    pagination_class = Pagination

    def get_context(self):
        return {"request": self.request, "view": self}

    def middleware(self, request, *args, **kwargs):
        """
        Returns the handler that will be dispatched. It allows to
        customize the handler based on arguments.

        To not override previous middleware when inheriting, call the
        parent's method before.
        handler = super().middleware(request, *args, **kwargs)

        Also note that a handler must always be returned.
        """
        if request.method.lower() in self.http_method_names:
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed
        return handler

    def trigger_handler(self, handler, request, *args, **kwargs):
        return handler(request, *args, **kwargs)

    def get_handler_args(self, *args, **kwargs):
        return args

    def get_handler_kwargs(self, *args, **kwargs):
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as RestFramework's dispatach method but
        it adds the possibility of adding custom handlers and customizing how the handler
        is triggered and what args and kwargs are passed.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)
            handler = self.middleware(request, *args, **kwargs)
            response = self.trigger_handler(
                handler,
                request,
                *self.get_handler_args(*args, **kwargs),
                **self.get_handler_kwargs(*args, **kwargs)
            )
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(
            request, response, *args, **kwargs)
        return self.response
    
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def get_serializer_context(self):
        return {
            "request": self.request,
        }

class InsecureView(View):
    permission_classes = []

class SecureView(View):
    permission_classes = [IsAuthenticated]

class SecureExtendedView(View):
    """
    SecureExtendedView provides two methods for each HTTP method. One if
    the user is authenticated and one if the user isn't. It can be used to
    provide different types of content depending on the user's permissions.
    """

    def get_public_handler(self, request):
        non_public_handler = getattr(
            self, request.method.lower(), None
        )
        handler = getattr(
            self, request.method.lower() + "_public", None
        )

        if handler is None and non_public_handler is None:
            self.http_method_not_allowed(request)
        elif handler is None:
            self.permission_denied(request)
        
        return handler

    def middleware(self, request, *args, **kwargs):
        # Run previous middleware
        handler = super().middleware(request, *args, **kwargs)
        if not request.user or isinstance(request.user, AnonymousUser):
            handler = self.get_public_handler(request)
        return handler

    def trigger_handler(self, handler, request, *args, **kwargs):
        try:
            return super().trigger_handler(handler, request, *args, **kwargs)
        except PermissionDenied:
            handler = self.get_public_handler(request)
            return handler(request, *args, **kwargs)
        
class ModelView(View):
    model_class = None
    queryset = None
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    lookup_fields = ["id"]
    lookup_translator = {}

    def __init__(self, *args, **kwargs):
        self._check_queryset()
        self._check_model_class()

    def _check_queryset(self):
        if self.queryset is None:
            raise IncorrectQuerysetException
        
        if not isinstance(self.queryset, models.QuerySet):
            raise IncorrectQuerysetException(message="Queryset must be of type django.db.models.QuerySet")

    def _check_model_class(self):
        if self.model_class is None:
            raise IncorrectModelException
        
        if type(self.model_class) != type(models.Model):
            raise IncorrectModelException(message="Model must be of type django.db.models.ModelBase")

    def get_model(self, request, *args, **kwargs) -> models.Model:
        return self.model_class
    
    def get_queryset(self, request, *args, **kwargs) -> models.QuerySet:
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, models.QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()

        return self.queryset

    def filter_queryset(self, request, queryset, *args, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        Filter based on request queries and program defined filters
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, queryset, self)

        for filter in kwargs.get("filters", []):
            queryset = queryset.filter(**filter)

        return queryset
    
    def get_lookup_kwargs(self, request, *args, **kwargs):
        """
        Generate lookup_kwargs for queryset filter from URL params.

        URL fields are defined in lookup_fields
        lookup_fields might correspond to a lookup_kwarg key, e.g. user_id -> pk
        The translation from lookup_fields is stored in lookup_translator
        """

        lookup_kwargs = {}

        for lookup_field in self.lookup_fields:
            value = kwargs.pop(lookup_field, None)
            if value is None:
                raise APIException(detail="Missing lookup values")
            
            key = lookup_field
            if lookup_field in self.lookup_translator.keys():
                key = self.lookup_translator[lookup_field]

            lookup_kwargs[key] = value

        return lookup_kwargs
    
    def get_obj(self, request, *args, **kwargs):
        model_class = self.get_model(request, *args, **kwargs)
        try:
            return self.get_queryset(request, *args, **kwargs).get(**self.get_lookup_kwargs(request, *args, **kwargs))
        except model_class.DoesNotExist:
            raise NotFound

class OrganizationModelView(ModelView, SecureView):
    organization_lookup_field = "organization_id"
    organization_lookup_arg = "organization"
    organization_serializer_field = "organization"

    HTTP_METHOD_TO_PERMISSIONS = {
        "get": "retrieve",
        "put": "update",
        "post": "create",
        "delete": "destroy",
    }

    def get_organization(self, request, *args, **kwargs):
        organization_id = kwargs.get(self.organization_lookup_field, "None")
        if organization_id == None:
            raise OrganizationLookupArgException
        
        try:
            return Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            raise NotFound
        
    def get_member(self, request, organization, *args, **kwargs):
        try:
            return Member.objects.get(user=request.user, organization=organization)
        except Member.DoesNotExist:
            raise NotFound

    def middleware(self, request, *args, **kwargs):
        handler = super().middleware(request, *args, **kwargs)

        model_class = self.get_model(request, *args, **kwargs)

        organization = self.get_organization(request, *args, **kwargs)
        member = self.get_member(request, organization, *args, **kwargs)

        setattr(request, "organization", organization)
        setattr(request, "member", member)

        if request.method.lower() not in self.HTTP_METHOD_TO_PERMISSIONS.keys():
            return self.http_method_not_allowed
        
        codename = self.HTTP_METHOD_TO_PERMISSIONS[request.method.lower()]
        permission = Permission.get_by_model(organization, codename, model_class)

        if not member.has_perm(permission):
            raise PermissionDenied
        
        return handler
    
    def get_queryset(self, request, *args, **kwargs):
        lookup_kwargs = {}
        lookup_kwargs[self.organization_lookup_arg] = request.organization
        return super().get_queryset(request, *args, **kwargs).filter(**lookup_kwargs)

    def get_lookup_kwargs(self, request, *args, **kwargs):
        lookup_kwargs = super().get_lookup_kwargs(request, *args, **kwargs)
        lookup_kwargs[self.organization_lookup_arg] = request.organization

        return lookup_kwargs
    
    def serializer_middleware(self, request, serializer, obj=None, *args, **kwargs):
        """
        Inject organization into serializer
        """
        serializer = super().serializer_middleware(request, serializer, obj=obj, *args, **kwargs)
        serializer.validated_data[self.organization_serializer_field] = request.organization
        return serializer