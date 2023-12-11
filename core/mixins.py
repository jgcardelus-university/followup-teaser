class BaseMixin(ModelView):
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._check_serializer_class()

    def _check_serializer_class(self):
        if self.serializer_class is None:
            raise IncorrectSerializerException

    def get_serializer(self, request, *args, **kwargs) -> serializers.Serializer:
        return self.serializer_class
    
    def serializer_middleware(self, request, serializer, obj=None, *args, **kwargs) -> serializers.Serializer:
        return serializer
    
    def after_save(self, request, serializer, obj=None, *args, **kwargs):
        pass
        
    def save(self, request, serializer, obj=None, *args, **kwargs):
        if serializer.is_valid():
            serializer = self.serializer_middleware(request, serializer, obj=obj, *args, **kwargs)
            serializer.save()
            self.after_save(request, serializer, obj=obj, *args, **kwargs)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, *args, **kwargs):
        obj = self.get_obj(request, *args, **kwargs)
        obj.delete()
        return Response(status.HTTP_204_NO_CONTENT)
    
class DetailMixin(BaseMixin):
    def detail(self, request, *args, **kwargs):
        obj = self.get_obj(request, *args, **kwargs)
        serializer_class = self.get_serializer(request, *args, **kwargs)
        serializer = serializer_class(obj, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class UpdateMixin(BaseMixin):
    def update(self, request, *args, **kwargs):
        obj = self.get_obj(request, *args, **kwargs)
        serializer_class = self.get_serializer(request, *args, **kwargs)
        serializer = serializer_class(obj, data=request.data, context=self.get_serializer_context())
        return self.save(request, serializer, obj, *args, **kwargs)
    
class PaginatedMixin(BaseMixin):
    def paginated_list(self, request, *args, **kwargs):
        queryset = self.get_queryset(request, *args, **kwargs)
        queryset = self.filter_queryset(request, queryset, *args, **kwargs)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer_class = self.get_serializer(request, *args, **kwargs)
        serializer = serializer_class(paginated_queryset, context=self.get_serializer_context(), many=True)
        return self.get_paginated_response(serializer.data)

class CreateMixin(BaseMixin):
    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer(request, *args, **kwargs)
        serializer = serializer_class(data=request.data, context=self.get_serializer_context())
        return self.save(request, serializer, None, *args, **kwargs)