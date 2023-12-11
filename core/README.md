### What gets called when a user requests a resource?

The stack for a user request is the following

-   View
-   Authentication (if the view is secured)
-   ModelView (if the view is tied to a model)
-   Authorization (check user permissions to that model)
-   Deserialization
-   Validation
-   Handling
-   Serialization
-   Response

### What's in this folder?

This folder shows snippets of Views, Mixins and Handlers.

Views:

They handle incoming requests. They decide which method must handle the request, they call the authentication and authorization backends and handle errors.

Handlers:

They are classes/methods that are called if more complex
logic has to be executed before a CRUD operation.

For example, invitations have to be validated before marking
them as accepted or rejected.

Mixins:

Many views perform the same function, apply CRUD operations to a model. The logic behind these operations is the same, so mixins abstract it and allow to write concise, powerful views.

For example, a Retrieve/Update/Delete view of an Apartment (a model) might lookg like this:

```python
class ApartmentRUDView(OrganizationModelView, DetailMixin, UpdateMixin):
    serializer_class = ApartmentSerializer
    model_class = Apartment
    queryset = Apartment.objects.all()

    def get(self, request, *args, **kwargs):
        return self.detail(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
```

In many views, deserialization, validation, handling, serialization and response are handed off to mixins.
